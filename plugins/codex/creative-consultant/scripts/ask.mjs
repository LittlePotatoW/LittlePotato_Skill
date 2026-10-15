#!/usr/bin/env node

import { readFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

const DEFAULT_SYSTEM_PROMPT = [
  'You are an imaginative creative-thinking partner.',
  'Explore unexpected connections, challenge familiar assumptions, and suggest fresh, useful directions.',
  'Stay grounded in the question and any supplied context. Clearly distinguish speculation from fact.'
].join(' ');

function fail(code, message, status) {
  const error = { code, message };
  if (status !== undefined) error.status = status;
  process.stdout.write(`${JSON.stringify({ ok: false, error })}\n`);
  process.exitCode = 1;
}

function validate(request) {
  if (!request || typeof request !== 'object' || Array.isArray(request)) {
    throw new Error('Request file must contain a JSON object.');
  }
  if (typeof request.question !== 'string' || request.question.trim() === '') {
    throw new Error('question must be a non-empty string.');
  }
  if (request.context !== undefined && typeof request.context !== 'string') {
    throw new Error('context must be a string.');
  }
  if (request.system_prompt !== undefined && typeof request.system_prompt !== 'string') {
    throw new Error('system_prompt must be a string.');
  }
  if (request.temperature !== undefined &&
      (typeof request.temperature !== 'number' || !Number.isFinite(request.temperature) ||
       request.temperature < 0 || request.temperature > 2)) {
    throw new Error('temperature must be a number from 0 to 2.');
  }
  if (request.model !== undefined &&
      (typeof request.model !== 'string' || request.model.trim() === '')) {
    throw new Error('model must be a non-empty string.');
  }
  if (request.max_tokens !== undefined &&
      (!Number.isInteger(request.max_tokens) || request.max_tokens < 1 || request.max_tokens > 393216)) {
    throw new Error('max_tokens must be an integer from 1 to 393216.');
  }
  if (request.stop !== undefined &&
      !(typeof request.stop === 'string' ||
        (Array.isArray(request.stop) && request.stop.length <= 16 && request.stop.every(x => typeof x === 'string')))) {
    throw new Error('stop must be a string or an array of up to 16 strings.');
  }
  if (request.response_format !== undefined && !['text', 'json_object'].includes(request.response_format)) {
    throw new Error('response_format must be "text" or "json_object".');
  }
  if (request.timeout_ms !== undefined &&
      (!Number.isInteger(request.timeout_ms) || request.timeout_ms < 1000 || request.timeout_ms > 300000)) {
    throw new Error('timeout_ms must be an integer from 1000 to 300000.');
  }
}

async function readJsonConfig(configPath) {
  try {
    return JSON.parse(await readFile(configPath, 'utf8'));
  } catch (error) {
    if (error.code === 'ENOENT') return {};
    throw new Error(`Could not read ${configPath}: ${error.message}`);
  }
}

async function readProjectEnv(envPath) {
  let contents;
  try {
    contents = await readFile(envPath, 'utf8');
  } catch (error) {
    if (error.code === 'ENOENT') return {};
    throw new Error(`Could not read ${envPath}: ${error.message}`);
  }

  const values = {};
  for (const [index, line] of contents.split(/\r?\n/).entries()) {
    const trimmed = line.trim();
    if (trimmed === '' || trimmed.startsWith('#')) continue;
    const match = trimmed.match(/^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/);
    if (!match) throw new Error(`Invalid .env.local entry on line ${index + 1}.`);
    let value = match[2].trim();
    if ((value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    values[match[1]] = value;
  }
  return values;
}

async function getProjectConfig() {
  const projectRoot = process.cwd();
  const projectConfig = await readJsonConfig(path.join(projectRoot, '.creative-consultant.json'));
  const projectEnv = await readProjectEnv(path.join(projectRoot, '.env.local'));
  return { projectConfig, projectEnv };
}

async function getUserDefaults() {
  const codexHome = process.env.CODEX_HOME || path.join(os.homedir(), '.codex');
  return readJsonConfig(path.join(codexHome, 'creative-consultant', 'config.json'));
}

async function main() {
  const requestPath = process.argv[2];
  if (!requestPath || process.argv.length !== 3) {
    fail('usage', 'Usage: node scripts/ask.mjs <request.json>');
    return;
  }

  let request;
  try {
    request = JSON.parse(await readFile(requestPath, 'utf8'));
    validate(request);
  } catch (error) {
    fail('invalid_request', error.message);
    return;
  }

  let project;
  let userDefaults;
  try {
    project = await getProjectConfig();
    userDefaults = await getUserDefaults();
  } catch (error) {
    fail('configuration_error', error.message);
    return;
  }

  const defaults = { ...userDefaults, ...project.projectConfig };
  const apiKey = project.projectEnv.DEEPSEEK_API_KEY ?? process.env.DEEPSEEK_API_KEY;
  if (!apiKey) {
    fail('missing_api_key', 'Set DEEPSEEK_API_KEY in the environment available to Codex.');
    return;
  }

  const model = request.model ?? defaults.model ?? 'deepseek-flash';
  const temperature = request.temperature ?? defaults.temperature ?? 1.5;
  const maxTokens = request.max_tokens ?? defaults.max_tokens ?? 4096;
  const timeoutMs = request.timeout_ms ?? defaults.timeout_ms ?? 60000;
  if (typeof model !== 'string' || model.trim() === '') {
    fail('configuration_error', 'Configured model must be a non-empty string.');
    return;
  }
  if (typeof temperature !== 'number' || !Number.isFinite(temperature) || temperature < 0 || temperature > 2) {
    fail('configuration_error', 'Configured temperature must be a number from 0 to 2.');
    return;
  }
  if (!Number.isInteger(maxTokens) || maxTokens < 1 || maxTokens > 393216) {
    fail('configuration_error', 'Configured max_tokens must be an integer from 1 to 393216.');
    return;
  }
  if (!Number.isInteger(timeoutMs) || timeoutMs < 1000 || timeoutMs > 300000) {
    fail('configuration_error', 'Configured timeout_ms must be an integer from 1000 to 300000.');
    return;
  }

  let systemPrompt = request.system_prompt ?? defaults.system_prompt ?? DEFAULT_SYSTEM_PROMPT;
  if ((request.response_format ?? 'text') === 'json_object') {
    systemPrompt += ' Respond with one valid JSON object.';
  }
  const userContent = request.context
    ? `Background:\n${request.context}\n\nQuestion:\n${request.question}`
    : request.question;
  const body = {
    model,
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userContent }
    ],
    temperature,
    max_tokens: request.max_tokens ?? defaults.max_tokens ?? 4096,
    stream: false,
    thinking: { type: 'disabled' },
    response_format: { type: request.response_format ?? 'text' }
  };
  if (request.stop !== undefined) body.stop = request.stop;

  let response;
  try {
    response = await fetch('https://api.deepseek.com/chat/completions', {
      method: 'POST',
      headers: {
        authorization: `Bearer ${apiKey}`,
        'content-type': 'application/json'
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(timeoutMs)
    });
  } catch (error) {
    if (error.name === 'TimeoutError') {
      fail('timeout', `DeepSeek request timed out after ${timeoutMs} ms.`);
      return;
    }
    const cause = error.cause;
    const causeDetails = [cause?.code, cause?.syscall, cause?.hostname].filter(Boolean).join(' ');
    fail('network_error', causeDetails
      ? `DeepSeek connection failed (${causeDetails}).`
      : `DeepSeek connection failed: ${error.message}`);
    return;
  }

  let data;
  try {
    data = await response.json();
  } catch {
    fail('invalid_response', `DeepSeek returned a non-JSON response (HTTP ${response.status}).`, response.status);
    return;
  }
  if (!response.ok) {
    const message = data?.error?.message ?? `DeepSeek request failed (HTTP ${response.status}).`;
    fail('api_error', message, response.status);
    return;
  }

  const choice = data?.choices?.[0];
  const content = choice?.message?.content;
  if (typeof content !== 'string') {
    fail('invalid_response', 'DeepSeek response did not include text content.', response.status);
    return;
  }

  process.stdout.write(`${JSON.stringify({
    ok: true,
    content,
    model: data.model ?? model,
    temperature,
    usage: data.usage ?? null,
    finish_reason: choice.finish_reason ?? null
  })}\n`);
}

main().catch(error => fail('unexpected_error', error.message));
