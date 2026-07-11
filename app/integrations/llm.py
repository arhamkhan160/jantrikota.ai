"""
integrations/llm.py
Provider-agnostic LLM caller with round-robin across multiple keys.

Any OpenAI-compatible endpoint works — OpenAI, Groq, OpenRouter, Together, or a
local server — by pointing LLM_BASE_URL at it. One SDK, swappable base_url.

Config (core/config.py):
  LLM_API_KEYS  — comma-separated keys, round-robined per call (spreads rate limits)
  LLM_API_KEY   — single key (used if LLM_API_KEYS is blank)
  LLM_MODEL     — model name (e.g. "llama-3.3-70b-versatile", "gpt-4o-mini")
  LLM_BASE_URL  — blank = OpenAI default; Groq / OpenRouter set their base

Round-robin assumes all keys hit the SAME provider (shared LLM_MODEL + LLM_BASE_URL).
# ponytail: per-key provider/model would need richer config — add when actually needed.
"""

import itertools
import json
import threading

from openai import OpenAI

from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)

_lock = threading.Lock()
_pool: list[OpenAI] | None = None
_rr: "itertools.count[int] | None" = None


def _llm_keys() -> list[str]:
    raw = (settings.LLM_API_KEYS or settings.LLM_API_KEY or "").strip()
    return [k.strip() for k in raw.split(",") if k.strip()]


def _build_pool() -> list[OpenAI]:
    keys = _llm_keys()
    if not keys:
        raise RuntimeError("No LLM key (LLM_API_KEYS / LLM_API_KEY) configured.")
    base = settings.LLM_BASE_URL or None
    logger.info(f"LLM pool: {len(keys)} key(s), round-robin per call.")
    return [OpenAI(api_key=k, base_url=base) for k in keys]


def _ordered_clients() -> list[OpenAI]:
    """Clients starting at the round-robin cursor, wrapping around (thread-safe)."""
    global _pool, _rr
    with _lock:
        if _pool is None:
            _pool, _rr = _build_pool(), itertools.count()
        n = len(_pool)
        start = next(_rr) % n
        return [_pool[(start + i) % n] for i in range(n)]


def complete_json(system: str, user: str, *, model: str | None = None) -> dict:
    """One structured call → parsed JSON dict. Deterministic (temperature=0).

    Round-robins the starting key each call; on failure (e.g. 429) rotates through
    the remaining keys before giving up.
    """
    last_err: Exception | None = None
    for client in _ordered_clients():
        try:
            resp = client.chat.completions.create(
                model=model or settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            return json.loads(resp.choices[0].message.content or "{}")
        except Exception as e:  # rate limit / transient — try the next key
            last_err = e
            logger.warning(f"LLM key failed, rotating to next: {e}")
    raise last_err  # all keys failed


# ── embeddings (own key; falls back to the first LLM key) ────────────────────

_embed_client_singleton: OpenAI | None = None


def _embed_client() -> OpenAI:
    global _embed_client_singleton
    if _embed_client_singleton is None:
        keys = _llm_keys()
        key = settings.EMBED_API_KEY or (keys[0] if keys else "")
        if not key:
            raise RuntimeError("No embedding key (EMBED_API_KEY / LLM_API_KEY[S]) configured.")
        base = settings.EMBED_BASE_URL or settings.LLM_BASE_URL or None
        _embed_client_singleton = OpenAI(api_key=key, base_url=base)
    return _embed_client_singleton


def embed(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. Raises RuntimeError if no key (caller falls back)."""
    resp = _embed_client().embeddings.create(model=settings.EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]
