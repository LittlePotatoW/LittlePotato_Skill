import test from 'node:test';
import assert from 'node:assert/strict';
import { polish } from '../scripts/polish.mjs';

const apiKey = 'mock-key-not-real';
const env = { ZHIPU_API_KEY: apiKey };
const response = (content, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  json: async () => content,
});

test('sends the supplied text to the documented endpoint and returns only polished content', async () => {
  let request;
  const result = await polish({ text: '原文', style: '正式', max_tokens: 1000 }, {
    env,
    fetchImpl: async (url, options) => {
      request = { url, ...options, body: JSON.parse(options.body) };
      return response({ choices: [{ message: { content: '润色结果' } }] });
    },
  });
  assert.equal(result, '润色结果');
  assert.equal(request.url, 'https://open.bigmodel.cn/api/paas/v4/chat/completions');
  assert.equal(request.headers.Authorization, `Bearer ${apiKey}`);
  assert.equal(request.body.model, 'glm-4.7-flash');
  assert.equal(request.body.max_tokens, 1000);
  assert.equal(request.body.messages[1].content, '原文');
  assert.match(request.body.messages[0].content, /正式/u);
  assert.equal(JSON.stringify(request.body).includes(apiKey), false);
});

test('uses default output limit and preserves long input without truncation', async () => {
  const longText = '长文本🙂'.repeat(50000);
  let body;
  await polish({ text: longText }, {
    env,
    fetchImpl: async (_url, options) => {
      body = JSON.parse(options.body);
      return response({ choices: [{ message: { content: '结果' } }] });
    },
  });
  assert.equal(body.max_tokens, 65536);
  assert.equal(body.messages[1].content, longText);
});

test('rejects empty text before making a request', async () => {
  let called = false;
  await assert.rejects(polish({ text: '  ' }, { env, fetchImpl: async () => { called = true; } }), /非空/u);
  assert.equal(called, false);
});

test('reports missing key without making a request', async () => {
  let called = false;
  await assert.rejects(polish({ text: '原文' }, { env: {}, cwd: 'C:/nonexistent-project', fetchImpl: async () => { called = true; } }), /缺少 ZHIPU_API_KEY/u);
  assert.equal(called, false);
});

test('maps request abort to a timeout message', async () => {
  await assert.rejects(polish({ text: '原文' }, {
    env,
    timeoutMs: 10,
    fetchImpl: async (_url, options) => new Promise((_resolve, reject) => {
      options.signal.addEventListener('abort', () => reject(Object.assign(new Error('aborted'), { name: 'AbortError' })), { once: true });
    }),
  }), /请求超时/u);
});

test('reports malformed API responses and empty results', async () => {
  await assert.rejects(polish({ text: '原文' }, { env, fetchImpl: async () => ({ ok: true, status: 200, json: async () => { throw new Error('invalid'); } }) }), /无效响应/u);
  await assert.rejects(polish({ text: '原文' }, { env, fetchImpl: async () => response({ choices: [{ message: { content: ' ' } }] }) }), /空文本/u);
});

test('explains server-side context and payload limits without echoing response content', async () => {
  await assert.rejects(polish({ text: '原文' }, {
    env,
    fetchImpl: async () => response({ error: { message: 'context length exceeded: sensitive echo' } }, 400),
  }), (error) => /缩短文本或拆分/u.test(error.message) && !error.message.includes('sensitive echo'));
  await assert.rejects(polish({ text: '原文' }, { env, fetchImpl: async () => response({}, 413) }), /拆分/u);
});

test('identifies GLM-4.7-Flash model load from BigModel error code 1305', async () => {
  await assert.rejects(polish({ text: '原文' }, {
    env,
    fetchImpl: async () => response({ error: { code: 1305, message: '该模型当前访问量过大，请您稍后再试' } }, 429),
  }), /当前访问量较大，请稍后重试/u);
});
