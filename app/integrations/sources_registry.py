"""
integrations/sources_registry.py
Dispatch dataset operations across sources by a ref of the form 'source:native_id'.

  openml:61                 -> OpenML dataset 61
  hf:imdb                   -> HuggingFace 'imdb'
  kaggle:uciml/iris         -> Kaggle 'uciml/iris'
  url:https://x.com/a.csv   -> direct URL

Each source module exposes search(query, limit), detail(native_id), fetch(native_id).
"""

from core.logger import get_logger
from integrations import openml as openml_source, hf, kaggle, url_source

logger = get_logger(__name__)

_SOURCES = {
    "openml": openml_source,
    "hf": hf,
    "kaggle": kaggle,
    "url": url_source,
}


def available() -> list[str]:
    return list(_SOURCES)


def _split(ref: str) -> tuple[str, str]:
    if ":" not in ref:
        raise ValueError(f"bad ref '{ref}', expected 'source:id'")
    src, native = ref.split(":", 1)   # split once — URLs contain ':'
    if src not in _SOURCES:
        raise ValueError(f"unknown source '{src}' (have: {', '.join(_SOURCES)})")
    return src, native


def search(query: str, limit: int = 10, sources: list[str] | None = None) -> list[dict]:
    sources = sources or ["openml"]   # OpenML is the ranked default; others opt-in
    hits: list[dict] = []
    for s in sources:
        mod = _SOURCES.get(s)
        if mod is None:
            logger.warning(f"skipping unknown source '{s}'")
            continue
        try:
            hits.extend(mod.search(query, limit))
        except Exception as e:  # a broken/unauthed source shouldn't sink the whole search
            logger.warning(f"{s} search failed: {e}")
    return hits


def detail(ref: str) -> dict:
    src, native = _split(ref)
    d = _SOURCES[src].detail(native)
    d.setdefault("ref", ref)
    return d


def fetch(ref: str):
    src, native = _split(ref)
    return _SOURCES[src].fetch(native)
