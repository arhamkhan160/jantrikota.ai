"""
integrations/hf.py
HuggingFace Hub dataset source. Public datasets, no auth.

No labeled target (HF datasets don't declare one) — the NLP/validation layer
resolves it. `datasets` / `huggingface_hub` imported lazily.
"""

from core.logger import get_logger

logger = get_logger(__name__)
SOURCE = "hf"


def search(query: str, limit: int = 10) -> list[dict]:
    from huggingface_hub import HfApi
    infos = HfApi().list_datasets(search=query, limit=limit)
    return [{
        "ref": f"{SOURCE}:{d.id}",
        "source": SOURCE,
        "name": d.id,
        "confidence": 0.0,   # HF search has no score; ordering is HF relevance
        "rows": None,
        "features": None,
    } for d in infos]


def detail(native_id: str) -> dict:
    from huggingface_hub import dataset_info
    info = dataset_info(native_id)
    card = info.cardData or {}
    description = card.get("pretty_name") or (card.get("annotations_creators") and native_id) or native_id

    columns = []
    try:  # cheap column peek via streaming — one row, no full download
        from datasets import load_dataset
        first = next(iter(load_dataset(native_id, split="train", streaming=True)))
        columns = [{
            "name": k, "type": type(v).__name__,
            "n_missing": None, "n_distinct": None, "explanation": None,
        } for k, v in first.items()]
    except Exception as e:  # some datasets need a config / aren't streamable
        logger.info(f"hf column peek skipped for {native_id}: {e}")

    return {
        "source": SOURCE, "ref": f"{SOURCE}:{native_id}", "name": native_id,
        "description": str(description), "target": None, "columns": columns,
    }


def fetch(native_id: str):
    from datasets import load_dataset
    ds = load_dataset(native_id, split="train")
    df = ds.to_pandas()
    logger.info(f"Fetched HF {native_id}: {df.shape}")
    return df, None
