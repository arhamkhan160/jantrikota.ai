"""
integrations/openml.py
Fetch datasets from OpenML.

OpenML labels the target column in metadata, so a fetched dataset flows straight
into validation + training with the target already known. `openml` is imported
lazily so it never slows app startup or tests that mock these functions.
"""

import pandas as pd

from core.logger import get_logger

logger = get_logger(__name__)


def _list():
    # ponytail: OpenML's client has no free-text search, so we pull the dataset
    # index once and filter client-side. Fine for now; add server-side search if slow.
    import openml
    return openml.datasets.list_datasets(output_format="dataframe")


def _get_dataset(openml_id: int):
    import openml
    return openml.datasets.get_dataset(openml_id)


def search(query: str, limit: int = 10) -> list[dict]:
    df = _list()
    hits = df[df["name"].str.contains(query, case=False, na=False)].head(limit)
    out = []
    for _, r in hits.iterrows():
        out.append({
            "openml_id": int(r["did"]),
            "name": str(r["name"]),
            "rows": int(r["NumberOfInstances"]) if pd.notna(r.get("NumberOfInstances")) else None,
            "features": int(r["NumberOfFeatures"]) if pd.notna(r.get("NumberOfFeatures")) else None,
        })
    return out


def fetch(openml_id: int) -> tuple[pd.DataFrame, str | None]:
    """Return (dataframe including target, target_column_name)."""
    ds = _get_dataset(openml_id)
    target = ds.default_target_attribute
    X, y, _, _ = ds.get_data(target=target)
    df = X.copy()
    if y is not None and target:
        df[target] = y
    logger.info(f"Fetched OpenML {openml_id}: {df.shape}, target={target}")
    return df, target
