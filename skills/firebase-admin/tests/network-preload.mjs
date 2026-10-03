// Test-only transport boundary: Google provider hosts are redirected to the loopback fixture.
// No CLI modules or credential adapters are mocked; loopback-only.cjs blocks every other host.
import http from 'node:http';
import https from 'node:https';
import { syncBuiltinESMExports } from 'node:module';

const fixture = new URL(process.env.TEST_PROVIDER_URL);
const providers = new Set([
  'identitytoolkit.googleapis.com',
  'firestore.googleapis.com',
  'storage.googleapis.com',
  'oauth2.googleapis.com',
  'www.googleapis.com',
]);
const request = http.request;
function transport(...args) {
  let options;
  let callback;
  if (typeof args[0] === 'string' || args[0] instanceof URL) {
    const url = new URL(args[0]);
    options = {
      protocol: url.protocol,
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      ...(typeof args[1] === 'object' ? args[1] : {}),
    };
    callback = typeof args[1] === 'function' ? args[1] : args[2];
  } else {
    options = { ...args[0] };
    callback = args[1];
  }
  const host = options.hostname ?? options.host;
  if (providers.has(host)) {
    options = {
      ...options,
      protocol: 'http:',
      hostname: '127.0.0.1',
      host: '127.0.0.1',
      port: fixture.port,
      agent: undefined,
      headers: { ...options.headers, 'x-test-provider-host': host },
    };
  }
  return request.call(http, options, callback);
}
http.request = transport;
https.request = transport;
http.get = https.get = (...args) => {
  const req = transport(...args);
  req.end();
  return req;
};
const fetch = globalThis.fetch;
globalThis.fetch = (input, init) => {
  const url = new URL(typeof input === 'string' || input instanceof URL ? input : input.url);
  if (!providers.has(url.hostname)) return fetch(input, init);
  const headers = new Headers(init?.headers ?? input?.headers);
  headers.set('x-test-provider-host', url.hostname);
  return fetch(new URL(url.pathname + url.search, fixture), { ...init, headers });
};
syncBuiltinESMExports();
