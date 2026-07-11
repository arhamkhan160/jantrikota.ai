"""
integrations/url_source.py
Load a dataset directly from a URL — the bounded, safe "web scraper".

Handles direct CSV/Excel/JSON, or the first HTML <table> on a page via
pandas.read_html. This is NOT arbitrary-page scraping (that's a separate,
much messier project). # ponytail: structured tables/files only.
"""

import pandas as pd

from core.logger import get_logger

logger = get_logger(__name__)
SOURCE = "url"


def search(query: str, limit: int = 10) -> list[dict]:
    return []   # URLs aren't searchable — you fetch a known URL directly


def _read(url: str) -> pd.DataFrame:
    low = url.lower().split("?")[0]
    if low.endswith(".csv"):
        return pd.read_csv(url)
    if low.endswith((".xlsx", ".xls")):
        return pd.read_excel(url)
    if low.endswith(".json"):
        return pd.read_json(url)
    tables = pd.read_html(url)   # HTML <table> elements
    if not tables:
        raise ValueError("no CSV/Excel/JSON extension and no HTML tables at URL")
    logger.info(f"url {url}: {len(tables)} HTML tables, using the first")
    return tables[0]


def detail(native_id: str) -> dict:
    df = _read(native_id).head(50)
    columns = [{
        "name": str(c), "type": str(df[c].dtype),
        "n_missing": int(df[c].isna().sum()), "n_distinct": int(df[c].nunique()),
        "explanation": None,
    } for c in df.columns]
    return {
        "source": SOURCE, "ref": f"{SOURCE}:{native_id}", "name": native_id,
        "description": f"Loaded from {native_id}", "target": None, "columns": columns,
    }


def fetch(native_id: str):
    df = _read(native_id)
    logger.info(f"Fetched URL {native_id}: {df.shape}")
    return df, None
