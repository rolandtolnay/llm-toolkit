import { readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import * as appSdk from 'firebase-admin/app';
import * as firestoreSdk from 'firebase-admin/firestore';
import { getMessaging } from 'firebase-admin/messaging';
import { CliError, classify, describe, invalid, text, type Options } from './shared.js';
import type { Services } from './services.js';

export async function runScript(services: Services, options: Options): Promise<unknown> {
  const code = text(options, 'code');
  const file = text(options, 'file');
  if ((code === undefined) === (file === undefined))
    invalid('Supply exactly one of --code JavaScript or --file UTF-8.js.');
  let source = code;
  if (file) {
    try {
      source = new TextDecoder('utf-8', { fatal: true }).decode(await readFile(file));
    } catch {
      throw new CliError('FILE_ERROR', 'Cannot read UTF-8 script file.');
    }
  }
  const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
  const { target } = services.resolved;
  // Trusted JavaScript, not a sandbox. require/import/process remain fully capable.
  const fn = new AsyncFunction('app', 'db', 'auth', 'storage', 'bucket', 'sdk', 'target', 'require', source);
  let result: unknown;
  try {
    result = await fn(
      services.app,
      services.firestore(),
      services.auth(),
      services.storage(),
      target.bucket ? services.storage().bucket(target.bucket) : null,
      { ...appSdk, ...firestoreSdk, getMessaging },
      target,
      createRequire(import.meta.url),
    );
  } catch (error) {
    // A script fails visibly, but nothing proves which of its writes landed first.
    const cause = classify(error, false);
    throw new CliError(
      'OUTCOME_UNKNOWN',
      'The script did not complete; writes it made may have committed. No automatic replay was attempted.',
      [`Script error (${cause.code}): ${describe(error)}`, ...(cause.suggestions ?? [])],
    );
  }
  return { value: result === undefined ? null : result };
}
