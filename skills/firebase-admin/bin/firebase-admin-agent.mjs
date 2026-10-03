#!/usr/bin/env node
try {
  const { main } = await import('../dist/cli.js');
  await main();
} catch {
  process.stdout.write(JSON.stringify({ success: false, command: 'startup', error: {
    code: 'SETUP_REQUIRED', message: 'CLI could not start. Run npm ci && npm run build in the installed firebase-admin skill directory.'
  } }) + '\n');
  process.exitCode = 1;
}
