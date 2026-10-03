import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { mkdtemp, mkdir, readFile, readdir, realpath, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { generateKeyPairSync } from 'node:crypto';

const skill = dirname(dirname(fileURLToPath(import.meta.url)));
export const secrets = {
  refresh: 'fake-selected-refresh-secret',
  access: 'fake-selected-access-secret',
  globalRefresh: 'fake-global-refresh-secret',
  globalAccess: 'fake-global-access-secret',
  adcRefresh: 'fake-adc-refresh-secret',
  adcAccess: 'fake-adc-access-secret',
  adcClient: 'fake-client-secret',
  password: 'fake-user-password-secret',
  hash: 'fake-password-hash-secret',
  salt: 'fake-password-salt-secret',
  download: 'fake-download-token-secret',
};
export function login(email = 'selected@example.test', refresh = secrets.refresh) {
  return {
    user: { email },
    tokens: { refresh_token: refresh, access_token: 'fake-expired-access-secret', expires_at: 1 },
  };
}
export function providerUser(uid = 'test-user') {
  return {
    localId: uid,
    email: 'user@example.test',
    emailVerified: true,
    displayName: 'Test User',
    createdAt: '1700000000000',
    lastLoginAt: '1700000010000',
    passwordHash: secrets.hash,
    salt: secrets.salt,
    password: secrets.password,
    providerUserInfo: [{ providerId: 'password', rawId: 'user@example.test', email: 'user@example.test' }],
  };
}
export function json(res, status, body) {
  res.writeHead(status, { 'content-type': 'application/json' });
  res.end(JSON.stringify(body));
}
export async function fixture(
  t,
  handler = (_request, res) => json(res, 500, { error: 'Unexpected provider request' }),
) {
  // process.cwd() canonicalizes macOS /var -> /private/var. Configstore directory keys must agree.
  const dir = await realpath(await mkdtemp(join(tmpdir(), 'firebase-admin-cli-test-')));
  const home = join(dir, 'home');
  const configHome = join(dir, 'config');
  const root = join(dir, 'consumer');
  const cwd = join(root, 'nested', 'working');
  await Promise.all([
    mkdir(home, { recursive: true }),
    mkdir(configHome, { recursive: true }),
    mkdir(cwd, { recursive: true }),
  ]);
  const requests = [];
  const handlerErrors = [];
  const server = createServer(async (req, res) => {
    let body = '';
    for await (const chunk of req) body += chunk;
    const record = {
      method: req.method,
      host: req.headers['x-test-provider-host'] ?? 'firebase-token-local',
      url: new URL(req.url, 'http://fixture.test'),
      headers: req.headers,
      body,
    };
    requests.push(record);
    try {
      await handler(record, res);
    } catch (error) {
      handlerErrors.push(error);
      json(res, 500, { error: 'Test fixture handler failed' });
    }
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const endpoint = `127.0.0.1:${server.address().port}`;
  const url = `http://${endpoint}`;
  t.after(async () => {
    await new Promise((resolve) => server.close(resolve));
    await rm(dir, { recursive: true, force: true });
  });
  async function put(path, data) {
    await mkdir(dirname(path), { recursive: true });
    await writeFile(path, typeof data === 'string' ? data : JSON.stringify(data));
    return path;
  }
  async function store(value) {
    return put(join(configHome, 'configstore', 'firebase-tools.json'), value);
  }
  await put(join(root, 'firebase.json'), {});
  await put(join(root, '.firebaserc'), { projects: { default: 'test-project' } });
  await store(login());
  async function run(args, env = {}) {
    const child = spawn(
      process.execPath,
      [
        '--require',
        join(skill, 'tests/loopback-only.cjs'),
        '--import',
        join(skill, 'tests/network-preload.mjs'),
        join(skill, 'bin/firebase-admin-agent.mjs'),
        ...args,
      ],
      {
        cwd,
        env: {
          PATH: process.env.PATH,
          HOME: home,
          XDG_CONFIG_HOME: configHome,
          CLOUDSDK_CONFIG: join(home, '.config/gcloud'),
          NO_PROXY: '*',
          GOOGLE_CLOUD_PROJECT: 'test-project',
          METADATA_SERVER_DETECTION: 'none',
          FIREBASE_TOKEN_URL: url,
          TEST_PROVIDER_URL: url,
          ...env,
        },
        stdio: ['ignore', 'pipe', 'pipe'],
      },
    );
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => {
      stdout += chunk;
    });
    child.stderr.on('data', (chunk) => {
      stderr += chunk;
    });
    const timer = setTimeout(() => child.kill('SIGKILL'), 15000);
    const status = await new Promise((resolve, reject) => {
      child.once('error', reject);
      child.once('close', resolve);
    });
    clearTimeout(timer);
    assert.notEqual(status, null, 'CLI process must finish without being killed');
    if (handlerErrors.length) throw handlerErrors[0];
    const lines = stdout.trim().split('\n');
    assert.equal(lines.length, 1, 'stdout must contain exactly one JSON envelope');
    const output = JSON.parse(lines[0]);
    const logs = [];
    async function collectLogs(path) {
      for (const entry of await readdir(path, { withFileTypes: true })) {
        const file = join(path, entry.name);
        if (entry.isDirectory()) await collectLogs(file);
        else if (entry.name.endsWith('.log')) logs.push(await readFile(file, 'utf8'));
      }
    }
    await collectLogs(dir);
    for (const secret of [...Object.values(secrets), 'fake-expired-access-secret']) {
      assert.equal(
        [stdout, stderr, ...logs].some((text) => text.includes(secret)),
        false,
        'CLI output/logs must not disclose fixture secrets',
      );
    }
    return { status, output, stderr };
  }
  async function serviceAccount() {
    const { privateKey } = generateKeyPairSync('rsa', {
      modulusLength: 2048,
      privateKeyEncoding: { type: 'pkcs8', format: 'pem' },
      publicKeyEncoding: { type: 'spki', format: 'pem' },
    });
    return put(join(dir, 'fake-service-account.json'), {
      type: 'service_account',
      project_id: 'credential-project',
      private_key: privateKey,
      client_email: 'fake-account@credential-project.iam.gserviceaccount.com',
    });
  }
  async function adc() {
    return put(join(home, '.config/gcloud/application_default_credentials.json'), {
      type: 'authorized_user',
      client_id: 'fake-client.apps.googleusercontent.com',
      client_secret: secrets.adcClient,
      refresh_token: secrets.adcRefresh,
    });
  }
  return { dir, home, root, cwd, endpoint, requests, put, store, run, serviceAccount, adc };
}
export function success(result, command) {
  assert.equal(result.status, 0);
  assert.equal(result.output.success, true);
  assert.equal(result.output.command, command);
  return result.output.result;
}
export function failure(result, command, code) {
  assert.equal(result.status, 1);
  assert.equal(result.output.success, false);
  assert.equal(result.output.command, command);
  assert.equal(result.output.error.code, code);
  assert.equal(Object.hasOwn(result.output, 'result'), false);
  return result.output.error;
}
export function refreshResponse(request, res) {
  assert.equal(request.method, 'POST');
  assert.match(request.body, /refresh_token/);
  json(res, 200, {
    access_token: request.body.includes(secrets.adcRefresh)
      ? secrets.adcAccess
      : request.body.includes(secrets.globalRefresh)
        ? secrets.globalAccess
        : secrets.access,
    expires_in: 3600,
    token_type: 'Bearer',
  });
}
