import type { Auth, UserRecord } from 'firebase-admin/auth';
import {
  CliError,
  classify,
  cursor,
  input,
  invalid,
  limit,
  object,
  pageInfo,
  required,
  text,
  uncursor,
  type Options,
} from './shared.js';

function user(u: UserRecord) {
  // Allowlist: UserRecord.toJSON() includes password hashes/salts on listUsers.
  return {
    uid: u.uid,
    email: u.email ?? null,
    emailVerified: u.emailVerified,
    displayName: u.displayName ?? null,
    phoneNumber: u.phoneNumber ?? null,
    photoURL: u.photoURL ?? null,
    disabled: u.disabled,
    metadata: { creationTime: u.metadata.creationTime, lastSignInTime: u.metadata.lastSignInTime ?? null },
    providerData: u.providerData.map((p) => ({
      uid: p.uid,
      providerId: p.providerId,
      email: p.email ?? null,
    })),
  };
}
export async function runAuth(
  auth: Auth,
  action: string,
  options: Options,
  target: unknown,
): Promise<unknown> {
  switch (action) {
    case 'get': {
      const choices = ['uid', 'email', 'phone'].filter((k) => text(options, k) !== undefined);
      if (choices.length !== 1) invalid('Select exactly one of --uid, --email or --phone.');
      const value = required(options, choices[0]);
      const record =
        choices[0] === 'uid'
          ? await auth.getUser(value)
          : choices[0] === 'email'
            ? await auth.getUserByEmail(value)
            : await auth.getUserByPhoneNumber(value);
      return { user: user(record) };
    }
    case 'list': {
      const size = limit(options);
      const scope = { target, action, size };
      const token = uncursor(text(options, 'after'), scope);
      if (token !== undefined && typeof token !== 'string') invalid('Invalid Auth continuation.');
      const page = await auth.listUsers(size, token);
      return {
        users: page.users.map(user),
        count: page.users.length,
        pageInfo: pageInfo(page.pageToken ? cursor(scope, page.pageToken) : null),
      };
    }
    case 'create':
      return { completed: true, user: user(await auth.createUser(object(await input(options)))) };
    case 'update':
      return {
        completed: true,
        user: user(await auth.updateUser(required(options, 'uid'), object(await input(options)))),
      };
    case 'delete':
      await auth.deleteUser(required(options, 'uid'));
      return { uid: required(options, 'uid'), completed: true };
    case 'claims-get':
      return {
        uid: required(options, 'uid'),
        claims: (await auth.getUser(required(options, 'uid'))).customClaims ?? null,
      };
    case 'claims-set': {
      const claims = await input(options);
      if (claims !== null) object(claims, 'Claims');
      await auth.setCustomUserClaims(required(options, 'uid'), claims);
      return { uid: required(options, 'uid'), completed: true };
    }
    case 'revoke':
      await auth.revokeRefreshTokens(required(options, 'uid'));
      return { uid: required(options, 'uid'), completed: true };
    case 'link': {
      const email = required(options, 'email');
      const kind = required(options, 'kind');
      const settings = await input(options, false);
      if (settings !== undefined) object(settings, 'ActionCodeSettings');
      let link: string;
      if (kind === 'reset-password') link = await auth.generatePasswordResetLink(email, settings);
      else if (kind === 'verify-email') link = await auth.generateEmailVerificationLink(email, settings);
      else if (kind === 'sign-in') {
        if (!settings) invalid('sign-in links require ActionCodeSettings via --data/--file.');
        link = await auth.generateSignInWithEmailLink(email, settings);
      } else if (kind === 'change-email')
        link = await auth.generateVerifyAndChangeEmailLink(email, required(options, 'new-email'), settings);
      else return invalid('--kind must be reset-password, verify-email, sign-in or change-email.');
      return { link, sensitive: true };
    }
    case 'custom-token': {
      const uid = required(options, 'uid');
      const claims = await input(options, false);
      if (claims !== undefined) object(claims, 'Claims');
      try {
        return {
          uid,
          token: await auth.createCustomToken(uid, claims),
          sensitive: true,
          tokenType: 'custom-token-not-id-token',
        };
      } catch (error) {
        const cause = classify(error, false);
        if (cause.code === 'INVALID_INPUT') throw cause;
        throw new CliError('SIGNING_FAILED', 'The selected identity could not sign a custom token.', [
          'Select a signing-capable service-account credential with --credential FILE, or configure the service identity and iam.serviceAccounts.signBlob permission outside this CLI. No identity was substituted.',
        ]);
      }
    }
    default:
      return invalid('Unknown Auth operation.');
  }
}
