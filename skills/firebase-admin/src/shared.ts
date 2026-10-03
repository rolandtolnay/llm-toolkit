import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';

export type ErrorCode =
  | 'INVALID_INPUT'
  | 'FILE_ERROR'
  | 'INVALID_CONFIG'
  | 'MISSING_PROJECT'
  | 'COMPATIBILITY_ERROR'
  | 'EMULATOR_REQUIRED'
  | 'AUTHENTICATION_FAILED'
  | 'PERMISSION_DENIED'
  | 'NOT_FOUND'
  | 'ALREADY_EXISTS'
  | 'PRECONDITION_FAILED'
  | 'UNSUPPORTED_VALUE'
  | 'SIGNING_FAILED'
  | 'OUTCOME_UNKNOWN'
  | 'PROVIDER_ERROR';

export class CliError extends Error {
  constructor(
    public code: ErrorCode,
    message: string,
    public suggestions?: string[],
  ) {
    super(message);
  }
}
export function invalid(message: string): never {
  throw new CliError('INVALID_INPUT', message);
}

type Known = {
  code: ErrorCode;
  matches: (code: unknown) => boolean;
  message: string;
  suggestions?: string[];
};
const codes =
  (...list: (number | string)[]) =>
  (code: unknown) =>
    list.includes(code as number | string);
// Deterministic provider failures: gRPC status numbers, HTTP statuses and SDK string codes.
const known: Known[] = [
  {
    code: 'NOT_FOUND',
    matches: codes(5, 404, 'NOT_FOUND', 'auth/user-not-found', 'storage/object-not-found'),
    message: 'The selected resource does not exist.',
  },
  {
    code: 'ALREADY_EXISTS',
    matches: codes(
      6,
      409,
      'ALREADY_EXISTS',
      'auth/uid-already-exists',
      'auth/email-already-exists',
      'auth/phone-number-already-exists',
    ),
    message: 'The selected resource already exists.',
  },
  {
    code: 'PRECONDITION_FAILED',
    matches: codes(9, 412, 'FAILED_PRECONDITION'),
    message: 'The precondition failed.',
    suggestions: [
      'For a write, read the current resource before repairing it. For a query, this code also reports a missing composite index.',
    ],
  },
  {
    code: 'PERMISSION_DENIED',
    matches: codes(7, 403, 'PERMISSION_DENIED', 'auth/insufficient-permission'),
    message: 'The selected identity lacks permission on the selected resource. No identity was substituted.',
    suggestions: [
      'Check IAM for this project and selected account. For Auth with end-user ADC, use ADC from your own OAuth client with Firebase Auth support, or explicitly select a service-account credential.',
    ],
  },
  {
    code: 'AUTHENTICATION_FAILED',
    matches: codes(16, 401, 'UNAUTHENTICATED', 'auth/invalid-credential', 'app/invalid-credential'),
    message: 'The selected credential was rejected. No fallback was attempted.',
    suggestions: [
      'For Firebase login, run firebase login --reauth. For ADC/Auth, use your own OAuth client ID or explicitly selected service-account credentials.',
    ],
  },
  {
    code: 'INVALID_INPUT',
    matches: (code) =>
      codes(3, 400, 'INVALID_ARGUMENT', 'auth/argument-error')(code) ||
      (typeof code === 'string' && code.startsWith('auth/invalid-')),
    message: 'The service rejected the input. Check field types, paths and command options.',
  },
];

export function describe(error: unknown): string {
  return error instanceof Error ? `${error.name}: ${error.message}` : String(error);
}

/** Map any thrown value onto the public error contract. `sent` means a mutating request may already have reached the service. */
export function classify(error: unknown, sent: boolean): CliError {
  if (error instanceof CliError) return error;
  const cause = (error as { cause?: unknown } | null)?.cause;
  if (cause instanceof CliError) return cause;
  const code = (error as { code?: unknown } | null)?.code;
  const match = known.find((k) => k.matches(code));
  if (match) return new CliError(match.code, match.message, match.suggestions);
  if (sent)
    return new CliError(
      'OUTCOME_UNKNOWN',
      'The request was not confirmed and may have completed. No automatic replay was attempted.',
      ['Inspect the named resource before retrying.'],
    );
  // SDK-side validation throws before any request and carries no code; its message names the caller's own input, never a credential.
  if (code === undefined) return new CliError('INVALID_INPUT', describe(error));
  return new CliError('PROVIDER_ERROR', 'The service request failed.', [
    'Check routing, connectivity, selected credentials and required Firestore indexes. Provider error bodies are suppressed to avoid exposing credentials or input data.',
  ]);
}

/** Wrap a deterministic-looking failure that happened after a write may have completed. */
export function uncertain(cause: CliError, message: string): CliError {
  if (cause.code === 'OUTCOME_UNKNOWN') return cause;
  return new CliError('OUTCOME_UNKNOWN', `${message} No automatic replay was attempted.`, [
    `Underlying failure: ${cause.code}. ${cause.message}`,
    ...(cause.suggestions ?? []),
    'Inspect the named resource before retrying.',
  ]);
}

export type Options = Record<string, string | boolean>;
export function text(options: Options, name: string): string | undefined {
  const value = options[name];
  if (value === undefined) return undefined;
  if (typeof value !== 'string' || !value) return invalid(`--${name} requires a value.`);
  return value;
}
export function required(options: Options, name: string): string {
  return text(options, name) ?? invalid(`Missing --${name}.`);
}
export function limit(options: Options, max = 1000): number {
  const n = Number(text(options, 'limit') ?? 25);
  if (!Number.isInteger(n) || n < 1 || n > max) invalid(`--limit must be 1..${max}.`);
  return n;
}
export async function input(options: Options, requiredInput = true): Promise<any> {
  const inline = text(options, 'data');
  const file = text(options, 'file');
  if (inline !== undefined && file !== undefined) invalid('Use --data or --file, not both.');
  if (inline === undefined && file === undefined) {
    if (requiredInput) invalid('Supply --data JSON or --file UTF-8.json.');
    return undefined;
  }
  let raw = inline;
  if (file) {
    try {
      raw = new TextDecoder('utf-8', { fatal: true }).decode(await readFile(file));
    } catch {
      throw new CliError('FILE_ERROR', 'Cannot read input file.', [
        'Check --file points to a readable UTF-8 file.',
      ]);
    }
  }
  try {
    return JSON.parse(raw!);
  } catch {
    return invalid('Input must be valid JSON.');
  }
}
export function object(value: any, label = 'Input'): Record<string, any> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) invalid(`${label} must be a JSON object.`);
  return value;
}
export function fingerprint(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(value)).digest('hex');
}
export function cursor(scope: unknown, value: unknown): string {
  return Buffer.from(JSON.stringify({ scope: fingerprint(scope), value })).toString('base64url');
}
export function uncursor(token: string | undefined, scope: unknown): any {
  if (!token) return undefined;
  try {
    const parsed = JSON.parse(Buffer.from(token, 'base64url').toString('utf8'));
    if (parsed.scope !== fingerprint(scope) || !('value' in parsed)) throw new Error();
    return parsed.value;
  } catch {
    return invalid(
      'Continuation does not match this target/query, or is invalid. Repeat the original options.',
    );
  }
}
export function pageInfo(next: string | null) {
  return { hasNextPage: next !== null, endCursor: next, consistency: 'live' };
}
