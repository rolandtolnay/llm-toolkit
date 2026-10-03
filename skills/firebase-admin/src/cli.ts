import { Console } from 'node:console';
import { resolveContext, route } from './context.js';
import { Services } from './services.js';
import { runFirestore } from './firestore.js';
import { runAuth } from './auth.js';
import { runStorage } from './storage.js';
import { runScript } from './exec.js';
import { encode } from './values.js';
import { CliError, classify, invalid, uncertain, type Options } from './shared.js';

const globals = [
  'project',
  'database',
  'bucket',
  'account',
  'credential',
  'adc',
  'emulator-only',
  'firestore-emulator',
  'auth-emulator',
  'storage-emulator',
];
const flags = new Set(['adc', 'emulator-only', 'help']);
// `compound` mutations read the resource back after writing, so a failure cannot prove the write failed.
type Command = { options: string[]; mutates?: 'single' | 'compound' };
const commands: Record<string, Command> = {
  context: { options: [] },
  exec: { options: ['code', 'file'] },
  'firestore collections': { options: ['path', 'limit', 'after'] },
  'firestore get': { options: ['path'] },
  'firestore query': { options: ['path', 'group', 'data', 'file', 'limit', 'after'] },
  'firestore count': { options: ['path', 'group', 'data', 'file'] },
  'firestore create': { options: ['path', 'data', 'file'], mutates: 'single' },
  'firestore replace': { options: ['path', 'data', 'file'], mutates: 'single' },
  'firestore merge': { options: ['path', 'data', 'file'], mutates: 'single' },
  'firestore patch': { options: ['path', 'data', 'file', 'precondition'], mutates: 'single' },
  'firestore delete': { options: ['path', 'precondition'], mutates: 'single' },
  'firestore batch': { options: ['data', 'file'], mutates: 'single' },
  'auth get': { options: ['uid', 'email', 'phone'] },
  'auth list': { options: ['limit', 'after'] },
  'auth create': { options: ['data', 'file'], mutates: 'compound' },
  'auth update': { options: ['uid', 'data', 'file'], mutates: 'compound' },
  'auth delete': { options: ['uid'], mutates: 'single' },
  'auth claims-get': { options: ['uid'] },
  'auth claims-set': { options: ['uid', 'data', 'file'], mutates: 'single' },
  'auth revoke': { options: ['uid'], mutates: 'single' },
  'auth custom-token': { options: ['uid', 'data', 'file'] },
  'auth link': { options: ['email', 'kind', 'new-email', 'data', 'file'] },
  'storage list': { options: ['prefix', 'limit', 'after'] },
  'storage metadata': { options: ['object'] },
  'storage download': { options: ['object', 'destination'] },
  'storage upload': { options: ['object', 'source', 'if-generation-match'], mutates: 'single' },
  'storage delete': { options: ['object', 'if-generation-match'], mutates: 'single' },
};
const help = {
  globals,
  commands: Object.fromEntries(Object.entries(commands).map(([name, command]) => [name, command.options])),
  input: '--data JSON or --file UTF-8.json; exec uses --code or --file',
  pagination: 'Repeat options with --after result.pageInfo.endCursor; reads are live.',
};

function parse(argv: string[]): { command: string; options: Options } {
  const words: string[] = [];
  const options: Options = {};
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (!arg.startsWith('--')) {
      words.push(arg);
      continue;
    }
    const name = arg.slice(2);
    if (Object.hasOwn(options, name)) invalid('Duplicate options are not accepted.');
    if (flags.has(name)) options[name] = true;
    else if (argv[i + 1] === undefined || argv[i + 1].startsWith('--'))
      invalid('An option is missing its value.');
    else options[name] = argv[++i];
  }
  const command = words.join(' ');
  if (options.help) return { command: 'help', options };
  if (!Object.hasOwn(commands, command)) invalid('Unknown command. Run --help for the Public CLI Contract.');
  const allowed = new Set([...globals, ...commands[command].options]);
  if (Object.keys(options).some((key) => !allowed.has(key)))
    invalid('An option is not supported by this command. Run --help.');
  return { command, options };
}

async function execute(command: string, options: Options): Promise<unknown> {
  if (command === 'help') return help;
  const resolved = await resolveContext(options);
  const [area, action] = command.split(' ');
  if (area === 'context') return resolved.target;
  route(resolved, area as 'firestore' | 'auth' | 'storage' | 'exec');
  const services = new Services(resolved);
  try {
    let result: unknown;
    if (area === 'firestore')
      result = await runFirestore(services.firestore(), action, options, resolved.target);
    else if (area === 'auth') result = await runAuth(services.auth(), action, options, resolved.target);
    else if (area === 'storage') {
      if (!resolved.target.bucket)
        invalid('Storage requires --bucket or a .firebase-admin.json bucket for this project.');
      result = await runStorage(
        services.storage().bucket(resolved.target.bucket),
        action,
        options,
        resolved.target,
      );
    } else result = await runScript(services, options);
    return { target: resolved.target, ...(result as Record<string, unknown>) };
  } finally {
    await services.close().catch(() => {});
  }
}

function fail(error: unknown, mutates: Command['mutates']): CliError {
  const cause = classify(error, mutates !== undefined);
  if (mutates === 'compound' && cause.code !== 'INVALID_INPUT' && cause.code !== 'ALREADY_EXISTS') {
    return uncertain(cause, 'Auth create/update failed, possibly after the write completed.');
  }
  return cause;
}

export async function main(argv = process.argv.slice(2)): Promise<void> {
  // All ordinary diagnostics, including script console.log, go to stderr; stdout holds one envelope.
  globalThis.console = new Console({ stdout: process.stderr, stderr: process.stderr });
  let command = 'invalid';
  try {
    const parsed = parse(argv);
    command = parsed.command;
    const result = await execute(command, parsed.options);
    process.stdout.write(JSON.stringify({ success: true, command, result: encode(result) }) + '\n');
  } catch (error) {
    const e = fail(error, commands[command]?.mutates);
    process.stdout.write(
      JSON.stringify({
        success: false,
        command,
        error: { code: e.code, message: e.message, ...(e.suggestions ? { suggestions: e.suggestions } : {}) },
      }) + '\n',
    );
    process.exitCode = 1;
  }
}
