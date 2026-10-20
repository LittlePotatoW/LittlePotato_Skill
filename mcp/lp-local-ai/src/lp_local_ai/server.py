"""lp-local-ai MCP 服务器。

本地 OCR（中英）+ 本地大模型工具（翻译/摘要/改写）。
LLM 由 Ollama 提供（OpenAI 兼容接口），OCR 由 RapidOCR 提供，
Ollama 默认连接本机 loopback 地址；如通过 LP_OLLAMA_BASE_URL 配置远程端点，LLM 输入文本会发送到该端点。

启动（stdio 传输）：
    uv run --project mcp/lp-local-ai lp-local-ai
"""

from __future__ import annotations

import os
from functools import lru_cache

import httpx
from mcp.server.mcpserver import MCPServer

import lp_local_ai.config as cfg

mcp = MCPServer(
    name="lp-local-ai",
    instructions=(
        "本机 AI 工具集：ocr_image 识别图片中的中英文字；"
        "translate / summarize / rewrite 调用 Ollama 模型处理文本（默认连接本机服务）。"
        "如配置 LP_OLLAMA_BASE_URL 为远程端点，文本会发送到该端点；请据此评估数据隐私。"
    ),
)


# ---------------------------------------------------------------------------
# 本地 LLM（Ollama OpenAI 兼容接口）
# ---------------------------------------------------------------------------

def _llm(system: str, user: str) -> str:
    """调用本地 Ollama 模型，返回纯文本；失败时返回可读的错误提示。"""
    url = f"{cfg.OLLAMA_BASE_URL}/v1/chat/completions"
    payload = {
        "model": cfg.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": cfg.LLM_TEMPERATURE,
        "max_tokens": cfg.LLM_MAX_TOKENS,
        "stream": False,
    }
    try:
        resp = httpx.post(url, json=payload, timeout=cfg.LLM_TIMEOUT)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except httpx.ConnectError:
        return (
            f"[本地模型不可用] 无法连接 Ollama（{cfg.OLLAMA_BASE_URL}）。"
            "请先启动 Ollama，并执行 `ollama pull qwen3:8b` 下载模型。"
        )
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:200]
        hint = ""
        if exc.response.status_code == 404:
            hint = f"（可能模型未下载，请执行 ollama pull {cfg.OLLAMA_MODEL}）"
        return f"[本地模型调用失败] HTTP {exc.response.status_code}{hint}: {detail}"
    except Exception as exc:  # noqa: BLE001
        return f"[本地模型调用失败] {exc}"


@mcp.tool()
def translate(text: str, target_lang: str = "中文") -> str:
    """把文本翻译成指定语言（默认中文），只输出译文；文本发往配置的 Ollama 服务。"""
    system = f"你是专业翻译。把用户文本翻译成{target_lang}，只输出译文，不要解释。"
    return _llm(system, text)


@mcp.tool()
def summarize(text: str, max_points: int = 8) -> str:
    """给长文本生成要点摘要，用简洁的 Markdown 列表输出。"""
    system = f"你是摘要助手。用不超过 {max_points} 条要点的 Markdown 列表总结用户文本。"
    return _llm(system, text)


@mcp.tool()
def rewrite(text: str, tone: str = "更正式、更通顺") -> str:
    """改写润色文本（默认更正式通顺），保持原意，只输出改写结果。"""
    system = f"你是文字润色助手。把用户文本改写得{tone}，保持原意，只输出改写结果。"
    return _llm(system, text)


# ---------------------------------------------------------------------------
# 本地 OCR（RapidOCR，中英）
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _ocr_engine():
    """懒加载 OCR 引擎：首次调用才导入，避免 MCP 服务启动变慢。"""
    try:
        from rapidocr import RapidOCR
    except ImportError as exc:
        raise RuntimeError(
            "未安装 rapidocr，请先执行: uv sync --project mcp/lp-local-ai"
        ) from exc
    return RapidOCR()


@mcp.tool()
def ocr_image(image_path: str) -> str:
    """识别本地图片中的中英文文字（jpg/png/bmp 等），返回按行排列的纯文本。"""
    if not os.path.isfile(image_path):
        return f"[OCR 失败] 文件不存在: {image_path}"
    try:
        engine = _ocr_engine()
        result = engine(image_path)[0]
    except Exception as exc:  # noqa: BLE001
        return f"[OCR 失败] {exc}"
    if not result:
        return "（未识别到文字）"
    return "\n".join(item[1] for item in result if len(item) >= 2 and item[1])


def main() -> None:
    """MCP 入口：stdio 传输，供 codex mcp / claude mcp 调用。"""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
