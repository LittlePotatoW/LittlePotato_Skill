# lp-local-ai

本地 AI 工具 MCP：**OCR（中英）+ 本地大模型（翻译/摘要/改写）**。
OCR 在本机处理。文本处理通过 Ollama 完成，默认连接本机地址 `http://127.0.0.1:11434`；如果配置远程 Ollama 地址，翻译、摘要和改写所用的文本会发送到该地址。请仅配置你信任且获准发送文本的服务端点。

## 工具列表

| 工具 | 说明 |
|------|------|
| `ocr_image` | 识别本地图片中的中英文文字，返回纯文本 |
| `translate` | 文本翻译（默认译成中文） |
| `summarize` | 长文本要点摘要 |
| `rewrite` | 文本改写润色 |

## 架构

```
Codex / Claude Code
        │  MCP (stdio)
        ▼
  lp-local-ai (本仓库 mcp/lp-local-ai)
        ├── OCR：RapidOCR（PP-OCRv6 中英模型，首次调用自动下载）
        └── LLM：Ollama 本地服务（默认模型 qwen3:8b）
```

## 硬件要求

- 建议 8GB 显存（RTX 5060 等）+ 16GB 内存
- 需要先安装 [Ollama](https://ollama.com)

## 快速开始

依赖安装有两种方式：**方式 A（uv，推荐）** 和 **方式 B（conda 全局环境，可选）**，任选其一；后面的模型准备与注册步骤通用。

### 1. 安装依赖（方式 A：uv）

在仓库根目录执行：

```bash
uv sync --project mcp/lp-local-ai
```

### 1b. 方式 B：conda 全局环境（可选）

想用 conda 统一管理 MCP 环境的话，在仓库根目录执行：

```bash
conda env create -f mcp/lp-local-ai/environment.yml
conda activate lp-mcp
```

注册时**不要用 `conda run`**（它对 stdio 协议有缓冲问题，会导致客户端收不到输出），直接用环境的 python.exe：

```bash
# 把 <Anaconda路径> 换成你机器上 Anaconda 的实际位置（Windows 默认 D:\Anaconda3）
codex mcp add lp-local-ai -- <Anaconda路径>\envs\lp-mcp\python.exe -m lp_local_ai.server
claude mcp add lp-local-ai -- <Anaconda路径>\envs\lp-mcp\python.exe -m lp_local_ai.server
```

冒烟测试在激活环境下直接执行：

```bash
python -c "from lp_local_ai.server import translate; print(translate('hello world'))"
```

环境的删除与更新：

```bash
conda env remove -n lp-mcp
conda env update -f mcp/lp-local-ai/environment.yml
```

### 2. 准备模型

```bash
# 本地大模型（约 5GB，Q4 量化）
ollama pull qwen3:8b

# OCR 模型无需手动下载：首次调用 ocr_image 时自动下载（约 30-100MB，只需联网一次）
```

### 3. 注册 MCP

在仓库根目录执行（`<仓库路径>` 换成实际绝对路径；路径含空格时务必加引号）：

```bash
# Codex
codex mcp add lp-local-ai -- uv run --project "<仓库路径>\mcp\lp-local-ai" lp-local-ai

# Claude Code
claude mcp add lp-local-ai -- uv run --project "<仓库路径>\mcp\lp-local-ai" lp-local-ai
```

重启客户端后即可使用。验证是否注册成功：

```bash
codex mcp list   # 或 claude mcp list
```

### 4. 手动验证

```bash
# 确认 Ollama 在线
curl http://127.0.0.1:11434/v1/models

# 冒烟测试 LLM 工具（依赖安装后）
uv run --project mcp/lp-local-ai python -c "from lp_local_ai.server import translate; print(translate('hello world'))"
```

## 配置（环境变量）

所有配置均通过环境变量传入，便于换机器、换模型：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LP_OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama 服务地址 |
| `LP_OLLAMA_MODEL` | `qwen3:8b` | 本地大模型名称 |
| `LP_LLM_TIMEOUT` | `120` | 单次调用超时（秒） |
| `LP_LLM_MAX_TOKENS` | `2048` | 输出上限（token） |
| `LP_LLM_TEMPERATURE` | `0.3` | 采样温度 |

示例（换用 14B 模型）：

```bash
set LP_OLLAMA_MODEL=qwen3:14b
```

如需使用远程 Ollama 服务，可将 `LP_OLLAMA_BASE_URL` 设置为该服务地址。配置此变量会使 `translate`、`summarize` 和 `rewrite` 将输入文本发送到配置的端点；默认值为本机 loopback 地址，不会将这些请求发往远程服务。配置远程端点前，请确认其数据处理和隐私策略符合你的要求。

## 常见问题

- **提示"无法连接 Ollama"**：先启动 Ollama（`ollama serve` 或打开 Ollama 桌面应用）。
- **提示 HTTP 404**：模型没下载，执行 `ollama pull <模型名>`。
- **想用 GPU 加速 OCR（可选）**：RapidOCR 默认 CPU 已足够快；批量处理时可切换 onnxruntime-gpu：

  ```bash
  cd mcp/lp-local-ai
  uv remove onnxruntime
  uv add onnxruntime-gpu
  ```

- **模型选择**：默认 `qwen3:8b` 是 8GB 显存下的甜点位；显存紧张可换 `qwen3:4b`。
