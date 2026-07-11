"""
integrations/openml.py
Fetch and discover datasets from OpenML.

Two-step discovery:
  search(q)      -> ranked top-N (id, name, confidence, rows, features), NO columns
  detail(id)     -> metadata only (description + columns), no full data download
  fetch(id)      -> full dataframe + target, for validation/training on commit

Ranking is semantic (query vs dataset names via embeddings), with a lexical
fallback when no embeddings key is configured. `openml` is imported lazily.
"""

import difflib

import numpy as np
import pandas as pd

from core.logger import get_logger
from integrations.llm import embed

logger = get_logger(__name__)

_POOL = 50   # lexical prefilter size before ranking


def _list():
    # ponytail: OpenML's client has no free-text search, so we pull the dataset
    # index once and filter client-side. Fine for now; add server-side search if slow.
    import openml
    return openml.datasets.list_datasets(output_format="dataframe")


def _get_dataset(openml_id: int, *, download_data: bool = True):
    import openml
    return openml.datasets.get_dataset(openml_id, download_data=download_data)


# ── ranking ──────────────────────────────────────────────────────────────────

def _rank_semantic(query: str, candidates: list[dict]) -> list[dict]:
    # ponytail: embeds names only (cheap). Embed descriptions if relevance needs it.
    vecs = embed([query] + [c["name"] for c in candidates])
    q = np.asarray(vecs[0], dtype=float)
    m = np.asarray(vecs[1:], dtype=float)
    sims = (m @ q) / (np.linalg.norm(m, axis=1) * np.linalg.norm(q) + 1e-9)
    for c, s in zip(candidates, sims):
        c["confidence"] = round(float((s + 1) / 2), 4)   # cosine [-1,1] -> [0,1]
    return sorted(candidates, key=lambda c: c["confidence"], reverse=True)


def _rank_lexical(query: str, candidates: list[dict]) -> list[dict]:
    ql = query.lower()
    for c in candidates:
        c["confidence"] = round(difflib.SequenceMatcher(None, ql, c["name"].lower()).ratio(), 4)
    return sorted(candidates, key=lambda c: c["confidence"], reverse=True)


def search(query: str, limit: int = 10) -> list[dict]:
    df = _list()
    tokens = [t for t in query.lower().split() if t]
    names = df["name"].astype(str)
    mask = names.str.lower().apply(lambda n: any(t in n for t in tokens)) if tokens else False
    pool = df[mask].head(_POOL)

    candidates = [{
        "openml_id": int(r["did"]),
        "name": str(r["name"]),
        "rows": int(r["NumberOfInstances"]) if pd.notna(r.get("NumberOfInstances")) else None,
        "features": int(r["NumberOfFeatures"]) if pd.notna(r.get("NumberOfFeatures")) else None,
    } for _, r in pool.iterrows()]

    if not candidates:
        return []

    try:
        ranked = _rank_semantic(query, candidates)
    except Exception as e:  # no key / provider has no embeddings endpoint
        logger.warning(f"semantic rank unavailable ({e}); using lexical fallback")
        ranked = _rank_lexical(query, candidates)

    return ranked[:limit]


# ── detail (metadata only) ───────────────────────────────────────────────────

def detail(openml_id: int) -> dict:
    ds = _get_dataset(openml_id, download_data=False)
    columns = []
    for f in ds.features.values():
        n_distinct = len(f.nominal_values) if getattr(f, "nominal_values", None) else None
        columns.append({
            "name": f.name,
            "type": getattr(f, "data_type", None),
            "n_missing": getattr(f, "number_missing_values", None),
            "n_distinct": n_distinct,
            "explanation": None,   # optionally filled by the LLM at the endpoint
        })
    return {
        "openml_id": openml_id,
        "name": ds.name,
        "description": ds.description,
        "target": ds.default_target_attribute,
        "columns": columns,
    }


# ── fetch full data (on commit) ──────────────────────────────────────────────

def fetch(openml_id: int) -> tuple[pd.DataFrame, str | None]:
    """Return (dataframe including target, target_column_name)."""
    ds = _get_dataset(openml_id, download_data=True)
    target = ds.default_target_attribute
    X, y, _, _ = ds.get_data(target=target)
    df = X.copy()
    if y is not None and target:
        df[target] = y
    logger.info(f"Fetched OpenML {openml_id}: {df.shape}, target={target}")
    return df, target
