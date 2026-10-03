import test from 'node:test';
import assert from 'node:assert/strict';
import { join } from 'node:path';
import { writeFile } from 'node:fs/promises';
import {
  fixture,
  login,
  secrets,
  providerUser,
  json,
  refreshResponse,
  success,
  failure,
} from './public-cli-fixture.mjs';

function isRefresh(r) {
  return r.url.pathname.includes('/token');
}
function authPath(r, project = 'test-project') {
  assert.equal(r.host, 'identitytoolkit.googleapis.com');
  assert.match(r.url.pathname, new RegExp(`^/v1/projects/${project}/accounts(?:[:/]|$)`));
  assert.equal(r.headers.authorization, `Bearer ${secrets.access}`);
}

test('pinned Firebase login refresh supports bounded Auth reads/update and suppresses sensitive user fields', async (t) => {
  let revokedAt;
  const startedAt = Math.floor(Date.now() / 1000);
  const f = await fixture(t, (r, res) => {
    if (isRefresh(r)) return refreshResponse(r, res);
    authPath(r, 'override-project');
    if (r.url.pathname.endsWith(':batchGet')) {
      assert.equal(r.url.searchParams.get('maxResults'), '1');
      json(res, 200, { users: [providerUser()], nextPageToken: 'provider-auth-next' });
    } else if (r.url.pathname.endsWith(':lookup')) json(res, 200, { users: [providerUser()] });
    else if (r.url.pathname.endsWith(':update')) {
      const input = JSON.parse(r.body);
      assert.equal(input.localId, 'test-user');
      if (Object.hasOwn(input, 'validSince')) revokedAt = input.validSince;
      else assert.equal(input.displayName, 'Updated User');
      json(res, 200, { localId: input.localId });
    } else assert.fail('Unexpected Auth operation');
  });
  await f.store({
    ...login('global@example.test', secrets.globalRefresh),
    additionalAccounts: [login()],
    activeAccounts: { [f.root]: 'selected@example.test' },
  });
  const options = ['--project', 'override-project'];
  const get = success(await f.run(['auth', 'get', '--uid', 'test-user', ...options]), 'auth get');
  assert.equal(get.target.project, 'override-project');
  assert.deepEqual(get.target.identity, { source: 'firebase-login', account: 'selected@example.test' });
  assert.equal(get.user.uid, 'test-user');
  assert.equal(Object.hasOwn(get.user, 'passwordHash'), false);
  const list = success(await f.run(['auth', 'list', '--limit', '1', ...options]), 'auth list');
  assert.equal(list.count, 1);
  assert.equal(list.users[0].uid, 'test-user');
  assert.equal(list.pageInfo.hasNextPage, true);
  assert.equal(list.pageInfo.consistency, 'live');
  assert.equal(typeof list.pageInfo.endCursor, 'string');
  const updated = success(
    await f.run([
      'auth',
      'update',
      '--uid',
      'test-user',
      '--data',
      JSON.stringify({ displayName: 'Updated User' }),
      ...options,
    ]),
    'auth update',
  );
  assert.equal(updated.completed, true);
  assert.equal(updated.user.uid, 'test-user');
  success(await f.run(['auth', 'revoke', '--uid', 'test-user', ...options]), 'auth revoke');
  assert.ok(
    Number.isInteger(revokedAt) && revokedAt >= startedAt && revokedAt <= Math.floor(Date.now() / 1000),
  );
  const refreshes = f.requests.filter(isRefresh);
  assert.equal(refreshes.length, 4, 'each isolated command refreshes the selected expired login once');
  for (const r of refreshes) {
    assert.equal(
      r.url.pathname,
      '/oauth2/v3/token',
      'exercise firebase-tools refresh, not an alternate credential implementation',
    );
    assert.ok(r.body.includes(secrets.refresh));
    assert.equal(r.body.includes(secrets.globalRefresh), false);
  }
});

test('Firebase login reaches a named Firestore database through the real REST/auth adapter', async (t) => {
  const name = 'projects/test-project/databases/named-db/documents/probes/one';
  const f = await fixture(t, (r, res) => {
    if (isRefresh(r)) return refreshResponse(r, res);
    assert.equal(r.host, 'firestore.googleapis.com');
    assert.equal(r.headers.authorization, `Bearer ${secrets.access}`);
    assert.equal(r.url.pathname, '/v1/projects/test-project/databases/named-db/documents:batchGet');
    assert.deepEqual(JSON.parse(r.body).documents, [name]);
    json(res, 200, [
      {
        found: {
          name,
          fields: { value: { stringValue: 'from-controlled-provider' } },
          createTime: '2024-01-01T00:00:00Z',
          updateTime: '2024-01-01T00:00:01Z',
        },
        readTime: '2024-01-01T00:00:02Z',
      },
    ]);
  });
  const result = success(
    await f.run(['firestore', 'get', '--path', 'probes/one', '--database', 'named-db']),
    'firestore get',
  );
  assert.equal(result.target.project, 'test-project');
  assert.equal(result.target.database, 'named-db');
  assert.equal(result.target.identity.source, 'firebase-login');
  assert.equal(result.path, 'probes/one');
  assert.equal(result.data.value, 'from-controlled-provider');
  assert.equal(f.requests.filter(isRefresh).length, 1);
  assert.equal(f.requests.filter((r) => !isRefresh(r)).length, 1);
});

test('large Firestore doubles can be copied and continued without becoming int64 or invalid input', async (t) => {
  let stored;
  let cursorSeen = false;
  const f = await fixture(t, (r, res) => {
    if (isRefresh(r)) return refreshResponse(r, res);
    const body = JSON.parse(r.body);
    if (r.url.pathname.endsWith(':commit')) {
      stored = body.writes[0].update.fields.n;
      return json(res, 200, {
        commitTime: '2024-01-01T00:00:01Z',
        writeResults: [{ updateTime: '2024-01-01T00:00:01Z' }],
      });
    }
    assert.ok(r.url.pathname.endsWith(':runQuery'));
    const start = body.structuredQuery.startAt;
    if (start) {
      cursorSeen = true;
      assert.equal(start.values[0].doubleValue, 1e20);
    }
    const docs = (start ? ['b'] : ['a', 'b']).map((id) => ({
      document: {
        name: `projects/test-project/databases/(default)/documents/items/${id}`,
        fields: { n: { doubleValue: 1e20 } },
        createTime: '2024-01-01T00:00:00Z',
        updateTime: '2024-01-01T00:00:01Z',
      },
      readTime: '2024-01-01T00:00:02Z',
    }));
    json(res, 200, docs);
  });
  const args = [
    'firestore',
    'query',
    '--path',
    'items',
    '--limit',
    '1',
    '--data',
    '{"orderBy":[{"field":"n"}]}',
  ];
  const first = success(await f.run(args), 'firestore query');
  const second = success(await f.run([...args, '--after', first.pageInfo.endCursor]), 'firestore query');
  assert.equal(second.documents[0].id, 'b');
  assert.equal(second.pageInfo.hasNextPage, false);
  success(
    await f.run([
      'firestore',
      'create',
      '--path',
      'items/copy',
      '--data',
      JSON.stringify(first.documents[0].data),
    ]),
    'firestore create',
  );
  assert.deepEqual(stored, { doubleValue: 1e20 });
  assert.equal(cursorSeen, true);
});

test('whole-number doubles keep their Firestore type across a native read/write round trip', async (t) => {
  const name = 'projects/test-project/databases/(default)/documents/prices/one';
  let written;
  const f = await fixture(t, (r, res) => {
    if (isRefresh(r)) return refreshResponse(r, res);
    if (r.url.pathname.endsWith(':commit')) {
      written = JSON.parse(r.body).writes[0].update.fields;
      return json(res, 200, {
        commitTime: '2024-01-01T00:00:01Z',
        writeResults: [{ updateTime: '2024-01-01T00:00:01Z' }],
      });
    }
    json(res, 200, [
      {
        found: {
          name,
          fields: {
            price: { doubleValue: 5 },
            count: { integerValue: '5' },
            ratio: { doubleValue: 2.5 },
            list: { arrayValue: { values: [{ doubleValue: 1 }] } },
          },
          createTime: '2024-01-01T00:00:00Z',
          updateTime: '2024-01-01T00:00:01Z',
        },
        readTime: '2024-01-01T00:00:02Z',
      },
    ]);
  });
  const read = success(await f.run(['firestore', 'get', '--path', 'prices/one']), 'firestore get');
  assert.deepEqual(read.data, {
    price: { $type: 'double', value: 5 },
    count: 5,
    ratio: 2.5,
    list: [{ $type: 'double', value: 1 }],
  });
  success(
    await f.run(['firestore', 'create', '--path', 'prices/copy', '--data', JSON.stringify(read.data)]),
    'firestore create',
  );
  assert.deepEqual(written, {
    price: { doubleValue: 5 },
    count: { integerValue: '5' },
    ratio: { doubleValue: 2.5 },
    list: { arrayValue: { values: [{ doubleValue: 1 }] } },
  });
});

test('exec failures report an unknown outcome with the script error visible', async (t) => {
  const f = await fixture(t);
  const demo = [
    '--project',
    'demo-exec',
    '--firestore-emulator',
    '127.0.0.1:1',
    '--auth-emulator',
    '127.0.0.1:1',
    '--storage-emulator',
    '127.0.0.1:1',
  ];
  const coded = failure(
    await f.run(['exec', '--code', 'const e = new Error("expected 3 docs"); e.code = 5; throw e', ...demo]),
    'exec',
    'OUTCOME_UNKNOWN',
  );
  assert.ok(coded.suggestions.some((s) => s.includes('NOT_FOUND')));
  assert.ok(coded.suggestions.some((s) => s.includes('expected 3 docs')));
  const typeError = failure(
    await f.run(['exec', '--code', 'const x = null; return x.y', ...demo]),
    'exec',
    'OUTCOME_UNKNOWN',
  );
  assert.ok(typeError.suggestions.some((s) => s.includes('TypeError')));
});

test('a rejected login refresh on Firestore reports the authentication failure, not an unknown commit', async (t) => {
  const f = await fixture(t, (r, res) => {
    assert.ok(isRefresh(r));
    json(res, 400, { error: 'invalid_grant' });
  });
  failure(
    await f.run(['firestore', 'get', '--path', 'probes/one']),
    'firestore get',
    'AUTHENTICATION_FAILED',
  );
  failure(
    await f.run(['firestore', 'create', '--path', 'probes/one', '--data', '{"a":1}']),
    'firestore create',
    'AUTHENTICATION_FAILED',
  );
  assert.equal(
    f.requests.filter((r) => !isRefresh(r)).length,
    0,
    'no Firestore request is sent without a token',
  );
});

test('Auth post-mutation lookup failure preserves uncertainty and underlying permission guidance', async (t) => {
  const writes = [];
  const f = await fixture(t, (r, res) => {
    if (isRefresh(r)) return refreshResponse(r, res);
    authPath(r);
    if (r.url.pathname.endsWith(':update')) {
      writes.push(JSON.parse(r.body));
      return json(res, 200, { localId: 'test-user' });
    }
    assert.ok(r.url.pathname.endsWith(':lookup'));
    json(res, 403, { error: { code: 403, message: 'INSUFFICIENT_PERMISSION' } });
  });
  const e = failure(
    await f.run(['auth', 'update', '--uid', 'test-user', '--data', '{"displayName":"Already changed"}']),
    'auth update',
    'OUTCOME_UNKNOWN',
  );
  assert.equal(writes.length, 1);
  assert.ok(e.suggestions.some((s) => s.includes('PERMISSION_DENIED')));
});

test('malformed UTF-8 mutation input is rejected before any provider access', async (t) => {
  const f = await fixture(t);
  const file = join(f.dir, 'malformed.json');
  await writeFile(file, Buffer.from('7b226e616d65223a22ff227d', 'hex'));
  failure(
    await f.run(['firestore', 'create', '--path', 'repairs/one', '--file', file]),
    'firestore create',
    'FILE_ERROR',
  );
  assert.equal(f.requests.length, 0);
});

test('selected login refresh rejection (including firebase-tools refresh-token sentinel) does not fall back to another account or ADC', async (t) => {
  const f = await fixture(t, (r, res) => {
    assert.ok(isRefresh(r));
    assert.ok(r.body.includes(secrets.refresh));
    json(res, 400, { error: 'invalid_grant', error_description: secrets.refresh });
  });
  await f.adc();
  await f.store({
    ...login('global@example.test', secrets.globalRefresh),
    additionalAccounts: [login()],
    activeAccounts: { [f.root]: 'selected@example.test' },
  });
  const error = failure(
    await f.run(['auth', 'get', '--uid', 'test-user']),
    'auth get',
    'AUTHENTICATION_FAILED',
  );
  assert.ok(error.suggestions.length > 0);
  assert.equal(f.requests.length, 1, 'refresh rejection must not reach Auth or try another credential');
});

test('login without a refresh token fails without consulting ADC or a different logged-in account', async (t) => {
  const f = await fixture(t);
  await f.adc();
  const selected = login();
  delete selected.tokens.refresh_token;
  await f.store({
    ...login('global@example.test', secrets.globalRefresh),
    additionalAccounts: [selected],
    activeAccounts: { [f.root]: 'selected@example.test' },
  });
  failure(await f.run(['auth', 'get', '--uid', 'test-user']), 'auth get', 'AUTHENTICATION_FAILED');
  assert.equal(f.requests.length, 0);
});

test('permission denial is distinct from an empty lookup and never substitutes credentials', async (t) => {
  const f = await fixture(t, (r, res) => {
    if (isRefresh(r)) return refreshResponse(r, res);
    authPath(r);
    json(res, 403, {
      error: {
        code: 403,
        message: 'INSUFFICIENT_PERMISSION',
        details: [{ diagnostic: 'detail fields are not forwarded' }],
      },
    });
  });
  await f.adc();
  await f.store({ ...login(), additionalAccounts: [login('other@example.test', secrets.globalRefresh)] });
  const error = failure(await f.run(['auth', 'get', '--uid', 'test-user']), 'auth get', 'PERMISSION_DENIED');
  assert.ok(error.suggestions.length > 0);
  assert.equal(f.requests.filter(isRefresh).length, 1);
  assert.equal(f.requests.filter((r) => !isRefresh(r)).length, 1);
});

test('provider error messages are forwarded with credential-shaped strings masked', async (t) => {
  const f = await fixture(t, (r, res) => {
    if (isRefresh(r)) return refreshResponse(r, res);
    json(res, 500, [
      {
        error: {
          code: 500,
          status: 'INTERNAL',
          message: 'BACKEND_DOWN ya29.planted-access-token 1//planted-refresh-token Bearer planted.bearer',
        },
      },
    ]);
  });
  const error = failure(
    await f.run(['firestore', 'get', '--path', 'probes/one']),
    'firestore get',
    'PROVIDER_ERROR',
  );
  assert.match(error.message, /BACKEND_DOWN/);
  assert.doesNotMatch(error.message, /planted/);
  assert.equal(error.message.match(/\[redacted-token\]/g)?.length, 3);
});

test('a query needing a composite index returns the link that creates it', async (t) => {
  const link =
    'https://console.firebase.google.com/v1/r/project/test-project/firestore/indexes?create_composite=ABC';
  const f = await fixture(t, (r, res) => {
    if (isRefresh(r)) return refreshResponse(r, res);
    json(res, 400, [
      {
        error: {
          code: 400,
          status: 'FAILED_PRECONDITION',
          message: `The query requires an index. You can create it here: ${link}`,
        },
      },
    ]);
  });
  const spec = { where: [{ field: 'a', op: '>=', value: 1 }], orderBy: [{ field: 'b' }] };
  const error = failure(
    await f.run(['firestore', 'query', '--path', 'records', '--data', JSON.stringify(spec)]),
    'firestore query',
    'PRECONDITION_FAILED',
  );
  assert.ok(error.message.includes(link));
});

test('explicit ADC performs OAuth from the isolated fake ADC file, not the available Firebase login', async (t) => {
  const f = await fixture(t, (r, res) => {
    if (isRefresh(r)) {
      assert.equal(r.host, 'oauth2.googleapis.com');
      assert.ok(r.body.includes(secrets.adcRefresh));
      return refreshResponse(r, res);
    }
    assert.equal(r.host, 'identitytoolkit.googleapis.com');
    assert.equal(r.headers.authorization, `Bearer ${secrets.adcAccess}`);
    json(res, 200, { users: [providerUser()] });
  });
  await f.adc();
  const result = success(await f.run(['auth', 'get', '--uid', 'test-user', '--adc']), 'auth get');
  assert.deepEqual(result.target.identity, { source: 'adc' });
  assert.equal(result.user.uid, 'test-user');
  assert.equal(f.requests.filter(isRefresh).length, 1);
  assert.equal(
    f.requests.some((r) => r.body.includes(secrets.refresh)),
    false,
  );
});

test('non-signing developer login returns actionable signing failure and cannot make external calls', async (t) => {
  const f = await fixture(t);
  const error = failure(
    await f.run(['auth', 'custom-token', '--uid', 'test-user']),
    'auth custom-token',
    'SIGNING_FAILED',
  );
  assert.ok(
    error.suggestions.some((s) => s.includes('--credential') && s.includes('iam.serviceAccounts.signBlob')),
  );
  assert.equal(f.requests.length, 0, 'must not refresh login or contact OAuth/Auth/IAM services');
});

test('ambiguous Firestore commit response is neither replayed nor reported successful', async (t) => {
  const f = await fixture(t, (r, res) => {
    res.writeHead(503, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ error: { code: 503, status: 'UNAVAILABLE', message: 'fake-private-payload' } }));
  });
  const result = await f.run(
    [
      'firestore',
      'create',
      '--path',
      'repairs/uncertain',
      '--data',
      '{"value":1}',
      '--project',
      'demo-boundary',
    ],
    { FIRESTORE_EMULATOR_HOST: f.endpoint },
  );
  failure(result, 'firestore create', 'OUTCOME_UNKNOWN');
  assert.equal(f.requests.length, 1);
  assert.match(f.requests[0].url.pathname, /:commit$/);
  assert.match(result.output.error.message, /fake-private-payload/, 'the service message is forwarded');
});

test('Storage sends the exact generation precondition and does not replay a rejected delete', async (t) => {
  const f = await fixture(t, (r, res) =>
    json(res, 412, { error: { code: 412, message: 'precondition failed' } }),
  );
  const result = await f.run(
    [
      'storage',
      'delete',
      '--bucket',
      'literal-bucket',
      '--object',
      'folder/file',
      '--if-generation-match',
      '9007199254740993',
      '--project',
      'demo-boundary',
    ],
    { FIREBASE_STORAGE_EMULATOR_HOST: f.endpoint },
  );
  failure(result, 'storage delete', 'PRECONDITION_FAILED');
  assert.equal(f.requests.length, 1);
  const [r] = f.requests;
  assert.equal(r.method, 'DELETE');
  assert.equal(r.url.searchParams.get('ifGenerationMatch'), '9007199254740993');
  assert.match(decodeURIComponent(r.url.pathname), /literal-bucket\/o\/folder\/file$/);
});

test('ambiguous auto-ID Auth creation sends one mutation and returns OUTCOME_UNKNOWN without replay', async (t) => {
  let creates = 0;
  const f = await fixture(t, (r, res) => {
    if (isRefresh(r)) return refreshResponse(r, res);
    authPath(r);
    assert.ok(r.url.pathname.endsWith('/accounts'));
    const input = JSON.parse(r.body);
    assert.equal(
      Object.hasOwn(input, 'localId'),
      false,
      'test the auto-ID mutation, where replay could create another user',
    );
    creates++;
    // The service may have committed; losing the response is not proof of rollback.
    res.destroy();
  });
  const error = failure(
    await f.run([
      'auth',
      'create',
      '--data',
      JSON.stringify({ email: 'new@example.test', password: secrets.password }),
    ]),
    'auth create',
    'OUTCOME_UNKNOWN',
  );
  assert.ok(error.suggestions.length > 0);
  assert.equal(creates, 1);
  assert.equal(f.requests.filter(isRefresh).length, 1);
});

test('Storage uses the selected login bridge, preserves bounded continuation and binds it to target and prefix', async (t) => {
  const f = await fixture(t, (r, res) => {
    if (isRefresh(r)) return refreshResponse(r, res);
    assert.equal(r.host, 'storage.googleapis.com');
    assert.equal(r.headers.authorization, `Bearer ${secrets.access}`);
    assert.equal(r.url.pathname, '/storage/v1/b/test-bucket/o');
    assert.equal(r.url.searchParams.get('maxResults'), '1');
    assert.equal(r.url.searchParams.get('prefix'), 'images/');
    const continued = r.url.searchParams.get('pageToken') === 'provider-storage-next';
    json(res, 200, {
      items: [
        {
          name: continued ? 'images/second.png' : 'images/first.png',
          bucket: 'test-bucket',
          generation: '123',
          size: '42',
          metadata: { firebaseStorageDownloadTokens: secrets.download },
        },
      ],
      ...(continued ? {} : { nextPageToken: 'provider-storage-next' }),
    });
  });
  const args = ['storage', 'list', '--bucket', 'test-bucket', '--prefix', 'images/', '--limit', '1'];
  const first = success(await f.run(args), 'storage list');
  assert.equal(first.target.bucket, 'test-bucket');
  assert.equal(first.count, 1);
  assert.equal(first.objects[0].name, 'images/first.png');
  assert.equal(Object.hasOwn(first.objects[0], 'metadata'), false);
  assert.equal(first.pageInfo.hasNextPage, true);
  assert.equal(f.requests.filter((r) => !isRefresh(r)).length, 1, 'must not exhaust all pages');
  const next = first.pageInfo.endCursor;
  const second = success(await f.run([...args, '--after', next]), 'storage list');
  assert.equal(second.objects[0].name, 'images/second.png');
  assert.equal(second.pageInfo.hasNextPage, false);
  assert.equal(second.pageInfo.endCursor, null);
  assert.equal(second.pageInfo.consistency, 'live');
  const before = f.requests.length;
  failure(
    await f.run([
      'storage',
      'list',
      '--bucket',
      'other-bucket',
      '--prefix',
      'images/',
      '--limit',
      '1',
      '--after',
      next,
    ]),
    'storage list',
    'INVALID_INPUT',
  );
  failure(
    await f.run([
      'storage',
      'list',
      '--bucket',
      'test-bucket',
      '--prefix',
      'other/',
      '--limit',
      '1',
      '--after',
      next,
    ]),
    'storage list',
    'INVALID_INPUT',
  );
  assert.equal(
    f.requests.length,
    before,
    'mismatched continuation fails before token refresh/provider request',
  );
});
