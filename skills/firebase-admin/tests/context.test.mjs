import test from 'node:test';
import assert from 'node:assert/strict';
import { join } from 'node:path';
import { fixture, login, secrets, success, failure } from './public-cli-fixture.mjs';

test('context inherits Firebase root, active alias/project and selected account from a nested consumer directory', async (t) => {
  const f = await fixture(t);
  await f.put(join(f.root, '.firebaserc'), {
    projects: { default: 'default-project', staging: 'active-project' },
  });
  await f.put(join(f.root, 'firebase.json'), { defaults: { project: 'legacy-project' } });
  await f.put(join(f.root, '.firebase-admin.json'), {
    'active-project': { database: 'named-db', bucket: 'configured-bucket' },
  });
  await f.store({
    ...login('global@example.test', secrets.globalRefresh),
    additionalAccounts: [login()],
    activeProjects: { [f.dir]: 'staging' },
    activeAccounts: { [f.root]: 'selected@example.test' },
  });
  const target = success(await f.run(['context']), 'context');
  assert.deepEqual(target, {
    project: 'active-project',
    database: 'named-db',
    bucket: 'configured-bucket',
    identity: { source: 'firebase-login', account: 'selected@example.test' },
    emulators: { firestore: null, auth: null, storage: null },
  });
  assert.equal(f.requests.length, 0, 'context inspection does not refresh credentials');
});

test('explicit project alias/account overrides are deterministic and do not inherit another project resource defaults', async (t) => {
  const f = await fixture(t);
  await f.put(join(f.root, '.firebaserc'), {
    projects: { default: 'default-project', other: 'override-project' },
  });
  await f.put(join(f.root, '.firebase-admin.json'), {
    'default-project': { database: 'default-db', bucket: 'default-bucket' },
  });
  await f.store({
    ...login(),
    additionalAccounts: [login('other@example.test', secrets.globalRefresh)],
    activeProjects: { [f.root]: 'default' },
    activeAccounts: { [f.root]: 'selected@example.test' },
  });
  const target = success(
    await f.run(['context', '--project', 'other', '--account', 'other@example.test']),
    'context',
  );
  assert.equal(target.project, 'override-project');
  assert.equal(target.database, '(default)');
  assert.equal(target.bucket, null);
  assert.deepEqual(target.identity, { source: 'firebase-login', account: 'other@example.test' });
  const explicit = success(
    await f.run([
      'context',
      '--project',
      'other',
      '--database',
      'explicit-db',
      '--bucket',
      'explicit-bucket',
    ]),
    'context',
  );
  assert.equal(explicit.database, 'explicit-db');
  assert.equal(explicit.bucket, 'explicit-bucket');
  assert.equal(f.requests.length, 0);
});

test('credential-file, environment credential and explicit ADC selection override an available Firebase login', async (t) => {
  const f = await fixture(t);
  const credential = await f.serviceAccount();
  await f.adc();
  const file = success(await f.run(['context', '--credential', credential]), 'context');
  assert.deepEqual(file.identity, { source: 'credential-file' });
  assert.equal(file.project, 'test-project', 'credential project does not override resolved target');
  const envFile = success(
    await f.run(['context'], { GOOGLE_APPLICATION_CREDENTIALS: credential }),
    'context',
  );
  assert.deepEqual(envFile.identity, { source: 'credential-file' });
  const adc = success(await f.run(['context', '--adc']), 'context');
  assert.deepEqual(adc.identity, { source: 'adc' });
  failure(
    await f.run(['context', '--adc', '--account', 'selected@example.test']),
    'context',
    'INVALID_INPUT',
  );
  failure(
    await f.run(['context', '--credential', join(f.dir, 'missing-key.json')]),
    'context',
    'AUTHENTICATION_FAILED',
  );
  assert.equal(f.requests.length, 0, 'selection and malformed credentials must not send provider requests');
});

test('missing, ambiguous and malformed configuration fail rather than choosing an unrelated project', async (t) => {
  const f = await fixture(t);
  await f.put(join(f.root, '.firebaserc'), {});
  failure(await f.run(['context']), 'context', 'MISSING_PROJECT');
  await f.put(join(f.root, '.firebaserc'), { projects: { one: 'first-project', two: 'second-project' } });
  failure(await f.run(['context']), 'context', 'MISSING_PROJECT');
  await f.put(join(f.root, '.firebaserc'), '{malformed');
  failure(await f.run(['context', '--project', 'explicit-project']), 'context', 'INVALID_CONFIG');
  await f.put(join(f.root, '.firebaserc'), {});
  await f.put(join(f.root, '.firebase-admin.json'), {
    'explicit-project': { bucket: 'x', collectionSuffix: '_dev' },
  });
  failure(await f.run(['context', '--project', 'explicit-project']), 'context', 'INVALID_INPUT');
  await f.put(join(f.root, '.firebase-admin.json'), { database: 'named-db' });
  failure(await f.run(['context', '--project', 'explicit-project']), 'context', 'INVALID_INPUT');
  assert.equal(f.requests.length, 0);
});

test('missing selected account does not use global login or ADC', async (t) => {
  const f = await fixture(t);
  await f.adc();
  await f.store({
    ...login('global@example.test', secrets.globalRefresh),
    activeAccounts: { [f.root]: 'missing@example.test' },
  });
  failure(await f.run(['context']), 'context', 'AUTHENTICATION_FAILED');
  failure(
    await f.run(['auth', 'get', '--uid', 'test-user', '--account', 'unknown@example.test']),
    'auth get',
    'AUTHENTICATION_FAILED',
  );
  assert.equal(f.requests.length, 0);
});

test('demo routing is fail-closed and reports explicit emulator endpoints without live credentials', async (t) => {
  const f = await fixture(t);
  const target = success(
    await f.run(['context', '--project', 'demo-test', '--auth-emulator', '127.0.0.1:9099']),
    'context',
  );
  assert.deepEqual(target.identity, { source: 'emulator' });
  assert.equal(target.emulators.auth, '127.0.0.1:9099');
  failure(
    await f.run(['auth', 'get', '--uid', 'test-user', '--project', 'demo-test']),
    'auth get',
    'EMULATOR_REQUIRED',
  );
  failure(
    await f.run([
      'exec',
      '--code',
      'return 1',
      '--project',
      'demo-test',
      '--auth-emulator',
      '127.0.0.1:9099',
    ]),
    'exec',
    'EMULATOR_REQUIRED',
  );
  failure(await f.run(['context', '--project', 'demo-test', '--adc']), 'context', 'INVALID_INPUT');
  failure(await f.run(['context', '--auth-emulator', 'https://localhost:9099']), 'context', 'INVALID_INPUT');
  assert.equal(f.requests.length, 0);
});
