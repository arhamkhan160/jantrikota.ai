"""
services/column_explainer.py
Optional LLM prose for dataset columns. Best-effort: OpenML rarely ships
per-column descriptions, so we generate one short sentence per column from the
dataset name/description + column names. Skipped silently if no LLM key.
"""

import json

from core.logger import get_logger
from integrations.llm import complete_json

logger = get_logger(__name__)

_SYSTEM = (
    "Explain each dataset column in ONE short plain-English sentence. "
    "Return JSON {\"explanations\": {\"<column>\": \"<sentence>\"}}. "
    "If a column's meaning is unclear from its name, say so briefly."
)


def explain(name: str, description: str | None, columns: list[str]) -> dict[str, str]:
    """{column: sentence}. Returns {} on any failure (LLM is optional here)."""
    try:
        user = json.dumps({"dataset": name, "description": description or "", "columns": columns})
        raw = complete_json(_SYSTEM, user)
        return raw.get("explanations", {}) or {}
    except Exception as e:  # no key / provider error — prose is optional
        logger.info(f"column explanations skipped: {e}")
        return {}
