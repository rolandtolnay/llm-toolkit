// Test-only outbound boundary: even SDK regressions cannot send emulator tests to live Firebase.
const net = require('node:net');
const dns = require('node:dns');
const allowed = new Set(['127.0.0.1', 'localhost', '::1']);
const check = (host) => {
  if (host && !allowed.has(host)) throw new Error('Test blocked non-loopback network');
};
const connect = net.Socket.prototype.connect;
net.Socket.prototype.connect = function (...args) {
  const normalized = Array.isArray(args[0]) ? args[0] : net._normalizeArgs(args);
  check(normalized[0]?.host);
  return connect.apply(this, args);
};
const lookup = dns.lookup;
dns.lookup = function (host, ...args) {
  check(host);
  return lookup.call(this, host, ...args);
};
