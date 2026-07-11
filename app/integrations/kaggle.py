"""
integrations/kaggle.py
Kaggle dataset source: search via the Kaggle API, download via kagglehub.

Needs KAGGLE_USERNAME / KAGGLE_KEY in the environment. Kaggle datasets are
arbitrary file dumps — we take the primary CSV and log when there are several.
No labeled target (validation resolves it).
"""

import glob
import os

import pandas as pd

from core.logger import get_logger

logger = get_logger(__name__)
SOURCE = "kaggle"


def _api():
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()   # reads KAGGLE_USERNAME / KAGGLE_KEY
    return api


def search(query: str, limit: int = 10) -> list[dict]:
    datasets = _api().dataset_list(search=query)[:limit]
    return [{
        "ref": f"{SOURCE}:{d.ref}",     # d.ref == "owner/slug"
        "source": SOURCE,
        "name": str(d.ref),
        "confidence": 0.0,
        "rows": None,
        "features": None,
    } for d in datasets]


def detail(native_id: str) -> dict:
    description = native_id
    try:
        files = _api().dataset_list_files(native_id).files
        description = f"{native_id} — files: {[f.name for f in files]}"
    except Exception as e:  # needs auth; columns require download (peeked on fetch)
        logger.info(f"kaggle detail limited for {native_id}: {e}")
    return {
        "source": SOURCE, "ref": f"{SOURCE}:{native_id}", "name": native_id,
        "description": description, "target": None, "columns": [],
    }


def fetch(native_id: str):
    import kagglehub
    path = kagglehub.dataset_download(native_id)
    csvs = sorted(glob.glob(os.path.join(path, "**", "*.csv"), recursive=True))
    if not csvs:
        raise ValueError(f"no CSV found in Kaggle dataset '{native_id}'")
    if len(csvs) > 1:
        logger.info(f"kaggle {native_id}: {len(csvs)} CSVs, using {os.path.basename(csvs[0])}")
    return pd.read_csv(csvs[0]), None
