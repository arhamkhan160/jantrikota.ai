"""
integrations/llm.py
Provider-agnostic LLM caller.

Any OpenAI-compatible endpoint works — OpenAI, Groq, OpenRouter, Together, or a
local server — by pointing LLM_BASE_URL at it. One SDK, swappable base_url; no
per-provider abstraction needed.

Config (core/config.py):
  LLM_API_KEY   — provider key
  LLM_MODEL     — model name (e.g. "llama-3.3-70b-versatile", "gpt-4o-mini")
  LLM_BASE_URL  — blank = OpenAI default; Groq="https://api.groq.com/openai/v1",
                  OpenRouter="https://openrouter.ai/api/v1"
"""

import json
from functools import lru_cache

from openai import OpenAI

from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)


@lru_cache
def _client() -> OpenAI:
    if not settings.LLM_API_KEY:
        raise RuntimeError("LLM_API_KEY is not set — configure it to use the NLP layer.")
    # base_url=None → SDK uses the OpenAI default endpoint.
    return OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL or None)


def complete_json(system: str, user: str, *, model: str | None = None) -> dict:
    """One structured call → parsed JSON dict. Deterministic (temperature=0)."""
    resp = _client().chat.completions.create(
        model=model or settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    content = resp.choices[0].message.content or "{}"
    return json.loads(content)
