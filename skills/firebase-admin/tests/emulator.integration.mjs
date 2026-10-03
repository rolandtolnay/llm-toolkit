import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const home = mkdtempSync(join(tmpdir(), 'firebase-agent-emulator-'));
const consumer = join(home, 'consumer');
mkdirSync(consumer);
writeFileSync(join(consumer, 'firebase.json'), '{}');
writeFileSync(join(consumer, '.firebaserc'), JSON.stringify({ projects: { default: 'demo-agent-cli' } }));
const env = {
  PATH: process.env.PATH,
  HOME: home,
  XDG_CONFIG_HOME: home,
  NODE_OPTIONS: `--require=${join(root, 'tests/loopback-only.cjs')}`,
  FIRESTORE_EMULATOR_HOST: process.env.FIRESTORE_EMULATOR_HOST,
  FIREBASE_AUTH_EMULATOR_HOST: process.env.FIREBASE_AUTH_EMULATOR_HOST,
  FIREBASE_STORAGE_EMULATOR_HOST: process.env.FIREBASE_STORAGE_EMULATOR_HOST,
};
for (const key of [
  'FIRESTORE_EMULATOR_HOST',
  'FIREBASE_AUTH_EMULATOR_HOST',
  'FIREBASE_STORAGE_EMULATOR_HOST',
]) {
  assert.match(env[key] ?? '', /^127\.0\.0\.1:\d+$/, `Run using npm run test:emulators (${key})`);
}
after(() => rmSync(home, { recursive: true, force: true }));
function call(args, success = true) {
  const child = spawnSync(process.execPath, [join(root, 'bin/firebase-admin-agent.mjs'), ...args], {
    cwd: consumer,
    env,
    encoding: 'utf8',
    timeout: 20000,
  });
  assert.ifError(child.error);
  const envelope = JSON.parse(child.stdout);
  assert.equal(envelope.success, success, child.stdout + child.stderr);
  assert.equal(child.status, success ? 0 : 1, child.stdout + child.stderr);
  assert.equal(child.stdout.trim().split('\n').length, 1);
  return { ...envelope, stderr: child.stderr };
}
const fs = (action, path, data, extra = [], success = true) =>
  call(
    [
      'firestore',
      action,
      ...(path ? ['--path', path] : []),
      ...(data === undefined ? [] : ['--data', JSON.stringify(data)]),
      ...extra,
    ],
    success,
  );
const get = (path) => fs('get', path).result;

test('native mutations distinguish set/update semantics, preconditions and atomicity', () => {
  fs('create', 'repairs/one', { keep: 1, profile: { remove: 'yes', retain: 'yes' }, nil: 'old' });
  assert.equal(fs('create', 'repairs/one', {}, [], false).error.code, 'ALREADY_EXISTS');
  fs('replace', 'repairs/one', { profile: { remove: 'yes', retain: 'yes' }, nil: 'old' });
  assert.equal(get('repairs/one').data.keep, undefined);
  fs('merge', 'repairs/one', { profile: { added: true } });
  assert.equal(get('repairs/one').data.profile.retain, 'yes');
  const prior = get('repairs/one').updateTime;
  fs(
    'patch',
    'repairs/one',
    { 'profile.remove': { $type: 'delete' }, nil: null, count: { $type: 'increment', value: 2 } },
    ['--precondition', JSON.stringify({ updateTime: prior })],
  );
  assert.deepEqual(get('repairs/one').data, { profile: { retain: 'yes', added: true }, nil: null, count: 2 });
  assert.equal(
    fs(
      'patch',
      'repairs/one',
      { nil: 'stale' },
      ['--precondition', JSON.stringify({ updateTime: prior })],
      false,
    ).error.code,
    'PRECONDITION_FAILED',
  );
  fs('patch', 'repairs/absent', { field: true }, [], false);
  fs('patch', 'repairs/one', { profile: { replaced: true } });
  assert.deepEqual(get('repairs/one').data.profile, { replaced: true });
  fs('create', 'repairs/one/children/kept', { survives: true });
  fs('delete', 'repairs/one');
  assert.equal(fs('get', 'repairs/one', undefined, [], false).error.code, 'NOT_FOUND');
  assert.equal(get('repairs/one/children/kept').data.survives, true);
  fs('merge', 'repairs/upsert', { created: true });
  const operations = [
    { op: 'create', path: 'repairs/atomic', data: { created: true } },
    { op: 'patch', path: 'repairs/missing', data: { invalid: true } },
  ];
  fs('batch', null, operations, [], false);
  fs('get', 'repairs/atomic', undefined, [], false);
  const tooMany = join(home, 'oversized.json');
  writeFileSync(
    tooMany,
    JSON.stringify(
      Array.from({ length: 501 }, (_, i) => ({ op: 'create', path: `oversized/${i}`, data: {} })),
    ),
  );
  assert.equal(call(['firestore', 'batch', '--file', tooMany], false).error.code, 'INVALID_INPUT');
  assert.equal(fs('count', 'oversized').result.count, 0);
  const committed = fs('batch', null, [
    { op: 'create', path: 'repairs/atomic', data: { done: true } },
    { op: 'patch', path: 'repairs/upsert', data: { done: true } },
  ]).result;
  assert.equal(committed.atomic, true);
  assert.equal(committed.writes.length, 2);
  assert.equal(get('repairs/upsert').data.done, true);
});

test('typed values roundtrip, transforms, tied pagination, projections and consumer query patterns', () => {
  const values = {
    timestamp: { $type: 'timestamp', seconds: 1700000000, nanoseconds: 123456000 },
    ref: { $type: 'reference', project: 'demo-agent-cli', database: '(default)', path: 'values/special' },
    binary: { $type: 'bytes', base64: 'AAH/' },
    geo: { $type: 'geopoint', latitude: 1.25, longitude: -7.5 },
    whole: { $type: 'double', value: 3 },
    fraction: 2.5,
    literal: { $type: 'map', value: { $type: 'timestamp', seconds: 'ordinary' } },
    big: { $type: 'integer', value: '9223372036854775807' },
  };
  fs('create', 'values/special', values);
  assert.deepEqual(get('values/special').data, values);
  fs('create', 'values/copy', get('values/special').data);
  assert.deepEqual(get('values/copy').data, values);
  assert.equal(
    fs('patch', 'values/copy', { timestamp: { $type: 'unknown' } }, [], false).error.code,
    'INVALID_INPUT',
  );
  assert.deepEqual(get('values/copy').data, values);
  fs('patch', 'values/copy', {
    tags: { $type: 'arrayUnion', values: ['a', 'b'] },
    updated: { $type: 'serverTimestamp' },
  });
  fs('patch', 'values/copy', { tags: { $type: 'arrayRemove', values: ['a'] } });
  assert.deepEqual(get('values/copy').data.tags, ['b']);
  assert.equal(get('values/copy').data.updated.$type, 'timestamp');
  fs(
    'batch',
    null,
    ['a', 'b', 'c', 'd'].map((id) => ({
      op: 'create',
      path: `pages/${id}`,
      data: { date: 1700000000, keywords: ['needle'], nested: { rating: 3 }, members: ['x'], label: id },
    })),
  );
  const spec = {
    where: [
      { field: 'date', op: '>=', value: 1700000000 },
      { field: 'keywords', op: 'array-contains', value: 'needle' },
    ],
    orderBy: [{ field: 'date', direction: 'asc' }],
    select: ['label'],
  };
  const first = fs('query', 'pages', spec, ['--limit', '2']).result;
  assert.equal(first.count, 2);
  assert.equal(first.pageInfo.hasNextPage, true);
  assert.deepEqual(
    first.documents.map((d) => d.data),
    [{ label: 'a' }, { label: 'b' }],
  );
  // Continuation holds values, not a reread of a now-deleted cursor document.
  fs('delete', 'pages/b');
  const second = fs('query', 'pages', spec, ['--limit', '2', '--after', first.pageInfo.endCursor]).result;
  assert.deepEqual(
    second.documents.map((d) => d.id),
    ['c', 'd'],
  );
  assert.equal(second.pageInfo.hasNextPage, false);
  assert.equal(second.pageInfo.endCursor, null);
  fs('query', 'other', spec, ['--after', first.pageInfo.endCursor], false);
  fs('query', 'pages', { ...spec, select: [] }, ['--after', first.pageInfo.endCursor], false);
  assert.equal(fs('count', 'pages', spec).result.count, 3);
  const nested = {
    where: [
      { field: 'nested.rating', op: '==', value: 3 },
      { field: 'members', op: 'array-contains-any', value: ['x', 'y'] },
    ],
  };
  assert.equal(fs('query', 'pages', nested).result.count, 3);
  fs('create', 'query-parents/one/query-children/child', { included: true });
  assert.equal(
    call(['firestore', 'query', '--group', 'query-children']).result.documents[0].path,
    'query-parents/one/query-children/child',
  );
  const discovery = fs('collections', null, undefined, ['--limit', '1']).result;
  assert.equal(discovery.count, 1);
  assert.equal(discovery.pageInfo.hasNextPage, true);
  const more = fs('collections', null, undefined, [
    '--limit',
    '1',
    '--after',
    discovery.pageInfo.endCursor,
  ]).result;
  assert.notEqual(more.collections[0].id, discovery.collections[0].id);
});

test('named database routing and raw async inline/file parity, diagnostics and visible failures', () => {
  const named = fs('create', 'routing/check', { named: true }, ['--database', 'named']).result;
  assert.equal(named.target.database, 'named');
  fs('get', 'routing/check', undefined, [], false);
  assert.equal(fs('get', 'routing/check', undefined, ['--database', 'named']).result.data.named, true);
  const code = `console.log('script diagnostic'); await db.runTransaction(async tx => { tx.update(db.doc('routing/check'), {raw: true}); }); return {project:app.options.projectId, database:db.databaseId, value:(await db.doc('routing/check').get()).data(), time:new sdk.Timestamp(1,123456789)};`;
  const raw = call(['exec', '--code', code, '--database', 'named']).result;
  assert.equal(raw.value.project, raw.target.project);
  assert.equal(raw.value.database, 'named');
  assert.equal(raw.value.value.raw, true);
  assert.deepEqual(raw.value.time, { $type: 'timestamp', seconds: 1, nanoseconds: 123456789 });
  const script = join(home, 'query.js');
  writeFileSync(
    script,
    `console.log('file diagnostic'); await Promise.resolve(); return (await db.doc('routing/check').get()).data();`,
  );
  const fromFile = call(['exec', '--file', script, '--database', 'named']);
  assert.equal(fromFile.result.value.raw, true);
  assert.match(fromFile.stderr, /file diagnostic/);
  call(['exec', '--file', script, '--code', 'return 1'], false);
  call(['exec', '--code', 'throw new Error("boom")'], false);
  call(['exec', '--code', 'return new Map()'], false);
  call(['exec', '--code', 'const cycle={};cycle.self=cycle;return cycle;'], false);
});

test('Auth user administration and sensitive outputs', () => {
  const a = call([
    'auth',
    'create',
    '--data',
    JSON.stringify({ uid: 'sample-one', email: 'sample@example.test', password: 'NotARoutineOutput123' }),
  ]);
  assert.equal(a.result.user.uid, 'sample-one');
  assert.ok(!JSON.stringify(a).includes('NotARoutineOutput123'));
  call(['auth', 'create', '--data', '{"uid":"sample-two"}']);
  call(['auth', 'update', '--uid', 'sample-one', '--data', '{"displayName":"Updated","disabled":true}']);
  assert.equal(call(['auth', 'get', '--email', 'sample@example.test']).result.user.displayName, 'Updated');
  const first = call(['auth', 'list', '--limit', '1']).result;
  const next = call(['auth', 'list', '--limit', '1', '--after', first.pageInfo.endCursor]).result;
  assert.equal(first.pageInfo.hasNextPage, true);
  assert.notEqual(first.users[0].uid, next.users[0].uid);
  // The Auth emulator can supply a token for a full final page; explicitly consume it.
  if (next.pageInfo.hasNextPage) {
    const end = call(['auth', 'list', '--limit', '1', '--after', next.pageInfo.endCursor]).result;
    assert.equal(end.pageInfo.hasNextPage, false);
    assert.equal(end.count, 0);
  }
  assert.ok(!JSON.stringify(first).match(/passwordHash|passwordSalt|NotARoutine/));
  call(['auth', 'claims-set', '--uid', 'sample-one', '--data', '{"role":"editor"}']);
  assert.equal(call(['auth', 'claims-get', '--uid', 'sample-one']).result.claims.role, 'editor');
  call(['auth', 'revoke', '--uid', 'sample-one']);
  const link = call(['auth', 'link', '--kind', 'reset-password', '--email', 'sample@example.test']).result;
  assert.equal(link.sensitive, true);
  assert.match(link.link, /oobCode=/);
  call(['auth', 'delete', '--uid', 'sample-two']);
  assert.equal(call(['auth', 'get', '--uid', 'sample-two'], false).error.code, 'NOT_FOUND');
});

test('Storage byte transfers, bounded pages, metadata redaction and generation preconditions', () => {
  const bucket = ['--bucket', 'demo-agent-cli.test'];
  const source = join(home, 'source.bin');
  const destination = join(home, 'download.bin');
  const bytes = Buffer.from([0, 255, 1, 2, 3]);
  writeFileSync(source, bytes);
  for (const name of ['files/a', 'files/b'])
    call(['storage', 'upload', '--source', source, '--object', name, ...bucket]);
  const first = call(['storage', 'list', '--prefix', 'files/', '--limit', '1', ...bucket]).result;
  assert.equal(first.count, 1);
  assert.equal(first.pageInfo.hasNextPage, true);
  const second = call([
    'storage',
    'list',
    '--prefix',
    'files/',
    '--limit',
    '1',
    '--after',
    first.pageInfo.endCursor,
    ...bucket,
  ]).result;
  assert.equal(second.pageInfo.hasNextPage, false);
  assert.notEqual(first.objects[0].name, second.objects[0].name);
  call(['storage', 'download', '--object', 'files/a', '--destination', destination, ...bucket]);
  assert.deepEqual(readFileSync(destination), bytes);
  const info = call(['storage', 'metadata', '--object', 'files/a', ...bucket]).result.object;
  assert.equal(Number(info.size), bytes.length);
  assert.equal(info.bucket, 'demo-agent-cli.test');
  call([
    'storage',
    'delete',
    '--object',
    'files/a',
    '--if-generation-match',
    String(info.generation),
    ...bucket,
  ]);
  call(['storage', 'metadata', '--object', 'files/a', ...bucket], false);
});
