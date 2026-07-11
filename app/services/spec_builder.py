"""
services/spec_builder.py
Turns a free-text query + dataset columns into a TaskSpec.

The LLM proposes {task, target, metric}; we then resolve the proposed target
against the REAL columns. Exact match wins; a close match (case/whitespace)
is salvaged; otherwise the spec is flagged ambiguous so the client can ask the
user which column to predict.
"""

import difflib

from core.constants import TaskType
from core.logger import get_logger
from integrations.llm import complete_json
from schemas.query import TaskSpec

logger = get_logger(__name__)

_DEFAULT_METRIC = {TaskType.CLASSIFICATION: "accuracy", TaskType.REGRESSION: "rmse"}

_SYSTEM = (
    "You map a machine-learning request to a JSON spec. "
    "Return ONLY JSON: {\"task\": \"classification\"|\"regression\", "
    "\"target\": \"<one of the given columns>\", "
    "\"metric\": \"accuracy\"|\"f1\"|\"roc_auc\"|\"rmse\"}. "
    "Pick target strictly from the provided column list."
)


def _resolve_target(proposed: str, columns: list[str]) -> str | None:
    """Exact match, else a close match (case/whitespace), else None."""
    if proposed in columns:
        return proposed
    lowered = {c.lower(): c for c in columns}
    if proposed.lower() in lowered:
        return lowered[proposed.lower()]
    close = difflib.get_close_matches(proposed, columns, n=1, cutoff=0.85)
    return close[0] if close else None


def build_spec(query: str, columns: list[str], dataset_id: str | None = None) -> TaskSpec:
    user = f"Columns: {columns}\nRequest: {query}"
    raw = complete_json(_SYSTEM, user)

    task = TaskType(raw.get("task", "classification"))
    proposed_target = str(raw.get("target", ""))
    metric = raw.get("metric") or _DEFAULT_METRIC[task]

    resolved = _resolve_target(proposed_target, columns)
    if resolved is None:
        # Can't trust the target — surface the closest columns for the user to pick.
        candidates = difflib.get_close_matches(proposed_target, columns, n=3, cutoff=0.3) or columns
        logger.info(f"Ambiguous target '{proposed_target}' not in columns; candidates={candidates}")
        return TaskSpec(
            task=task, target=proposed_target, metric=metric,
            dataset_id=dataset_id, ambiguous=True, candidates=candidates,
        )

    return TaskSpec(task=task, target=resolved, metric=metric, dataset_id=dataset_id)
