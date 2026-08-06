"""lp-local-ai 配置：全部走环境变量，便于跨机器分享。

所有变量均以 LP_ 为前缀，未设置时使用默认值。
"""

from __future__ import annotations

import os

# Ollama 服务地址（OpenAI 兼容接口）
OLLAMA_BASE_URL = os.environ.get("LP_OLLAMA_BASE_URL", "http://127.0.0.1:11434")

# 本地大模型名称
OLLAMA_MODEL = os.environ.get("LP_OLLAMA_MODEL", "qwen3:8b")

# 单次 LLM 调用超时（秒）
LLM_TIMEOUT = float(os.environ.get("LP_LLM_TIMEOUT", "120"))

# 单次 LLM 输出上限（token）
LLM_MAX_TOKENS = int(os.environ.get("LP_LLM_MAX_TOKENS", "2048"))

# LLM 采样温度
LLM_TEMPERATURE = float(os.environ.get("LP_LLM_TEMPERATURE", "0.3"))
