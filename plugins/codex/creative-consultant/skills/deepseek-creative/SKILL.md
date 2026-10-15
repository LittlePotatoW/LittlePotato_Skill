---
name: deepseek-creative
description: Send one explicitly requested creative consultation to DeepSeek and return its response to Codex. Use only when the user explicitly invokes this skill.
---

# DeepSeek Creative Consultation

Use this skill only when explicitly invoked by the user. Make exactly one DeepSeek API request per invocation.

Infer the useful question from the user's request and the current conversation. Decide whether relevant background would improve the answer. Include only the smallest useful summary or specific excerpts; never assume that the whole conversation or workspace should be sent. Do not read files only to build context unless they are relevant to the user's question.

Use a high-variation creative framing: invite unexpected connections, challenge familiar assumptions, and offer fresh directions while keeping the answer relevant to the request. The default temperature is 1.5. Honor a temperature the user specifies for this call. Temperature must be between 0 and 2. The API request disables DeepSeek thinking mode because temperature has no effect in thinking mode.

Write a UTF-8 JSON request file in the system temporary directory. Resolve the installed script at `plugins/cache/littlepotato-skill-local/creative-consultant/local/scripts/ask.mjs` below `CODEX_HOME` (or `~/.codex` if it is unset), then run that single Node.js command with a one-time sandbox escalation and the request file path. Do not add a reusable approval rule or prefix. This runs the command outside the sandbox with the current Windows user's permissions; the user must approve each invocation. If approval is denied, stop without sending the request. Remove the temporary request file after the call. Do not put the API key in the request file or command line. The script returns JSON on standard output. Read and use its `content` as internal input for the current task; decide how much of the response is useful to present to the user. If the call fails, report the concise error and do not retry unless the user asks.

Request fields:

- `question` (required): the question to send.
- `context` (optional): background text selected for this request.
- `system_prompt` (optional): replace the default creative system prompt.
- `temperature`, `model`, `max_tokens`, `stop`, and `response_format` (optional): per-request settings; default values are in the plugin README.
