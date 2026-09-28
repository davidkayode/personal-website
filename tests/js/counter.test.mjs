// Runs site/script.js against a fake browser: node --test tests/js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const SCRIPT = readFileSync(new URL('../../site/script.js', import.meta.url), 'utf8');

async function runPage(responses) {
  const calls = [];
  const counter = { textContent: '' };
  const listeners = {};
  const warnings = [];
  const fetch = async (url, options = {}) => {
    calls.push({ url, method: options.method || 'GET' });
    const reply = responses[url];
    if (!reply) return { ok: false, status: 404, json: async () => ({}) };
    return { ok: reply.status === 200, status: reply.status, json: async () => reply.body };
  };
  const window = { addEventListener: (event, fn) => { listeners[event] = fn; } };
  const context = {
    window,
    document: { querySelector: (sel) => (sel === '.counter' ? counter : null) },
    fetch,
    console: { warn: (...a) => warnings.push(a.join(' ')), error: (...a) => warnings.push(a.join(' ')), log() {} },
  };
  vm.runInNewContext(SCRIPT, context);
  await listeners.load();
  await new Promise((resolve) => setTimeout(resolve, 0));
  return { calls, counter, warnings };
}

test('reads the API URL from /config.json and shows the count', async () => {
  const api = 'https://api.example/prod/count';
  const page = await runPage({
    '/config.json': { status: 200, body: { counterApiUrl: api } },
    [api]: { status: 200, body: { value: 786 } },
  });
  assert.deepEqual(page.calls, [{ url: '/config.json', method: 'GET' }, { url: api, method: 'POST' }]);
  assert.equal(page.counter.textContent, 786);
});

test('missing config leaves the footer blank and never calls an API', async () => {
  const page = await runPage({});
  assert.deepEqual(page.calls.map((c) => c.url), ['/config.json']);
  assert.equal(page.counter.textContent, '');
  assert.ok(page.warnings.length > 0);
});

test('config without a URL does not POST anywhere', async () => {
  const page = await runPage({ '/config.json': { status: 200, body: {} } });
  assert.equal(page.calls.filter((c) => c.method === 'POST').length, 0);
  assert.equal(page.counter.textContent, '');
});

test('an API error leaves the footer blank without throwing', async () => {
  const api = 'https://api.example/prod/count';
  const page = await runPage({ '/config.json': { status: 200, body: { counterApiUrl: api } }, [api]: { status: 500, body: {} } });
  assert.equal(page.counter.textContent, '');
  assert.ok(page.warnings.some((w) => w.includes('500')));
});
