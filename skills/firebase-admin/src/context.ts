import { existsSync, readFileSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';
import { createRequire } from 'node:module';
import { applicationDefault, cert, type Credential } from 'firebase-admin/app';
import { GoogleAuth, OAuth2Client } from 'google-auth-library';
import { CliError, invalid, object, text, type Options } from './shared.js';

const require = createRequire(import.meta.url);
const SCOPES = [
  'https://www.googleapis.com/auth/cloud-platform',
  'https://www.googleapis.com/auth/firebase',
  'https://www.googleapis.com/auth/userinfo.email',
];
export interface Target {
  project: string;
  database: string;
  bucket: string | null;
  identity: { source: string; account?: string };
  emulators: { firestore: string | null; auth: string | null; storage: string | null };
}
export interface Resolved {
  target: Target;
  credential: Credential;
  googleAuth: GoogleAuth;
  emulatorOnly: boolean;
}
function config(path: string): any {
  if (!existsSync(path)) return {};
  try {
    return object(JSON.parse(readFileSync(path, 'utf8')), 'Configuration');
  } catch {
    throw new CliError('INVALID_CONFIG', 'Invalid JSON configuration.', [
      'Check firebase.json, .firebaserc and .firebase-admin.json.',
    ]);
  }
}
function nonempty(v: any, label: string): string {
  if (typeof v !== 'string' || !v.trim()) invalid(`${label} must be a nonempty string.`);
  return v;
}
function endpoint(v: string | undefined): string | null {
  if (v === undefined) return null;
  if (!/^(localhost|127\.0\.0\.1|\[::1\]|[a-zA-Z0-9.-]+):[0-9]+$/.test(v))
    invalid('Emulator endpoints must be host:port without a scheme.');
  const port = Number(v.slice(v.lastIndexOf(':') + 1));
  if (port < 1 || port > 65535) invalid('Invalid emulator port.');
  return v;
}
function loginFailure(): CliError {
  return new CliError(
    'AUTHENTICATION_FAILED',
    'The selected Firebase login could not supply a valid access token. No other identity was tried.',
    ['Run firebase login --reauth for the selected account, or explicitly select --credential FILE / --adc.'],
  );
}

/**
 * Compatibility adapter for the pinned firebase-tools; never loads its CLI entry point/loggers.
 * This file, services.ts and firestore.ts rely on internals of the exact versions pinned in package.json.
 * After upgrading any of them, rerun `npm test` and `npm run test:emulators`, then repeat a live read
 * of Firestore and Auth with a Firebase login; a passing build alone proves nothing.
 */
export async function resolveContext(options: Options, cwd = process.cwd()): Promise<Resolved> {
  require('firebase-tools/lib/logger').logger.silent = true;
  const { configstore } = require('firebase-tools/lib/configstore');
  const firebaseAuth = require('firebase-tools/lib/auth');
  const root = require('firebase-tools/lib/detectProjectRoot').detectProjectRoot({ cwd }) as
    string | undefined;
  const directory = root ?? resolve(cwd);
  const rc = config(join(directory, '.firebaserc'));
  const firebase = config(join(directory, 'firebase.json'));
  // Optional resource defaults keyed by project ID, so nothing leaks across targets.
  const local = config(join(directory, '.firebase-admin.json'));
  const aliases = object(rc.projects ?? {}, '.firebaserc projects');
  let active: string | undefined;
  const projects = configstore.get('activeProjects') ?? {};
  for (let p = directory; ; p = dirname(p)) {
    if (projects[p]) {
      active = projects[p];
      break;
    }
    if (dirname(p) === p) break;
  }
  // Mirrors Command.applyRC: explicit > inherited active > legacy defaults > single alias/default.
  let selected = text(options, 'project') ?? active ?? firebase.defaults?.project;
  if (selected) selected = Object.hasOwn(aliases, selected) ? aliases[selected] : selected;
  else selected = Object.keys(aliases).length === 1 ? Object.values(aliases)[0] : aliases.default;
  if (!selected)
    throw new CliError('MISSING_PROJECT', 'No unambiguous Firebase project selected.', [
      'Pass --project PROJECT_ID or use firebase use in this repository.',
    ]);
  const project = nonempty(selected, 'Project');
  if (!/^[a-z][a-z0-9-]*$/.test(project))
    invalid('Use a literal project ID or configured alias, not a project number.');
  const scoped = object(local[project] ?? {}, '.firebase-admin.json entry');
  if (Object.keys(scoped).some((k) => !['database', 'bucket'].includes(k)))
    invalid('.firebase-admin.json entries accept only database and bucket.');
  const database = nonempty(text(options, 'database') ?? scoped.database ?? '(default)', 'Database');
  const bucketValue = text(options, 'bucket') ?? scoped.bucket;
  const bucket = bucketValue === undefined ? null : nonempty(bucketValue, 'Bucket');
  if (database.includes('/') || (bucket && /[/:]/.test(bucket)))
    invalid('Database and bucket must be literal names, not URLs or paths.');
  const emulators = {
    firestore: endpoint(text(options, 'firestore-emulator') ?? process.env.FIRESTORE_EMULATOR_HOST),
    auth: endpoint(text(options, 'auth-emulator') ?? process.env.FIREBASE_AUTH_EMULATOR_HOST),
    storage: endpoint(text(options, 'storage-emulator') ?? process.env.FIREBASE_STORAGE_EMULATOR_HOST),
  };
  // Do not let a second Storage SDK environment variable contradict the reported endpoint.
  if (
    process.env.STORAGE_EMULATOR_HOST &&
    process.env.STORAGE_EMULATOR_HOST !== `http://${emulators.storage}`
  )
    invalid(
      'STORAGE_EMULATOR_HOST conflicts with explicit Firebase Storage routing. Use --storage-emulator host:port.',
    );
  const emulatorOnly = options['emulator-only'] === true || project.startsWith('demo-');
  const accountOption = text(options, 'account');
  const key = text(options, 'credential');
  if ([!!accountOption, !!key, options.adc === true].filter(Boolean).length > 1)
    invalid('Choose only one of --account, --credential or --adc.');
  let identity: Target['identity'];
  let credential: Credential;
  let googleAuth: GoogleAuth;
  const fakeCredential = { getAccessToken: async () => ({ access_token: 'owner', expires_in: 3600 }) };
  if (emulatorOnly) {
    if (accountOption || key || options.adc)
      invalid('Emulator-only mode does not accept live credential selection.');
    identity = { source: 'emulator' };
    credential = fakeCredential;
    const client = new OAuth2Client();
    client.setCredentials({ access_token: 'owner', expiry_date: Date.now() + 3600000 });
    googleAuth = new GoogleAuth({ authClient: client, projectId: project });
  } else if (key || options.adc || (!accountOption && process.env.GOOGLE_APPLICATION_CREDENTIALS)) {
    const file = key ?? (options.adc ? undefined : process.env.GOOGLE_APPLICATION_CREDENTIALS);
    identity = { source: file ? 'credential-file' : 'adc' };
    try {
      credential = file ? cert(file) : applicationDefault();
      googleAuth = new GoogleAuth({ ...(file ? { keyFile: file } : {}), scopes: SCOPES, projectId: project });
    } catch {
      throw new CliError('AUTHENTICATION_FAILED', 'Cannot load selected credentials.', [
        'Use a readable service-account JSON file, or --adc for Application Default Credentials.',
      ]);
    }
  } else {
    const selectedEmail = accountOption ?? (root ? configstore.get('activeAccounts')?.[root] : undefined);
    const account = selectedEmail
      ? firebaseAuth.getAllAccounts().find((a: any) => a.user.email === selectedEmail)
      : firebaseAuth.getProjectDefaultAccount(root);
    if (!account && (selectedEmail || configstore.get('user') || configstore.get('tokens')))
      throw loginFailure();
    if (account) {
      identity = { source: 'firebase-login', account: account.user.email };
      credential = {
        async getAccessToken() {
          try {
            const refresh = account.tokens.refresh_token;
            if (!refresh) throw loginFailure();
            const token = await firebaseAuth.getAccessToken(refresh, SCOPES);
            // firebase-tools can return the refresh token as an access token on HTTP 400/401.
            if (
              !token.access_token ||
              token.access_token === refresh ||
              !Number.isFinite(token.expires_at) ||
              token.expires_at <= Date.now()
            )
              throw loginFailure();
            return {
              access_token: token.access_token,
              expires_in: Math.floor((token.expires_at - Date.now()) / 1000),
            };
          } catch {
            throw loginFailure();
          }
        },
      };
      const client = new OAuth2Client();
      client.refreshHandler = async () => {
        const token = await credential.getAccessToken();
        return { access_token: token.access_token, expiry_date: Date.now() + token.expires_in * 1000 };
      };
      googleAuth = new GoogleAuth({ authClient: client, projectId: project });
    } else {
      identity = { source: 'adc' };
      credential = applicationDefault();
      googleAuth = new GoogleAuth({ scopes: SCOPES, projectId: project });
    }
  }
  return { target: { project, database, bucket, identity, emulators }, credential, googleAuth, emulatorOnly };
}

export function route(r: Resolved, service: 'firestore' | 'auth' | 'storage' | 'exec'): void {
  const needed = service === 'exec' ? (['firestore', 'auth', 'storage'] as const) : [service];
  if (r.emulatorOnly && needed.some((s) => !r.target.emulators[s]))
    throw new CliError(
      'EMULATOR_REQUIRED',
      'Emulator-only/demo operation requires explicit endpoints for every accessed service.',
      [
        'Set FIRESTORE_EMULATOR_HOST, FIREBASE_AUTH_EMULATOR_HOST and FIREBASE_STORAGE_EMULATOR_HOST as applicable. Raw execution requires all three.',
      ],
    );
  // Explicit endpoint flags reach the SDKs through the only switch they expose: environment variables.
  const { firestore, auth, storage } = r.target.emulators;
  if (firestore) process.env.FIRESTORE_EMULATOR_HOST = firestore;
  if (auth) process.env.FIREBASE_AUTH_EMULATOR_HOST = auth;
  if (storage) {
    process.env.FIREBASE_STORAGE_EMULATOR_HOST = storage;
    process.env.STORAGE_EMULATOR_HOST = `http://${storage}`;
  }
}
