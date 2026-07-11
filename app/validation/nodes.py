"""
validation/nodes.py
Graph nodes for the validation agent.

Flow: profile -> review (LLM) -> gate (stats) -> [ask_user] -> apply -> loop.
The LLM only proposes; gate.py decides what's allowed; the user confirms drops.
"""

import json

import pandas as pd
from langgraph.types import interrupt

from core.logger import get_logger
from integrations.llm import complete_json
from validation import store
from validation.gate import gate
from validation.profiler import profile as compute_profile

logger = get_logger(__name__)

MAX_ITERATIONS = 10   # loop guard: stop even if the LLM keeps proposing

_REVIEW_SYSTEM = (
    "You are a dataset-validation reviewer. Given a statistical profile, propose "
    "cleaning actions as JSON: {\"proposals\": [{\"col\": <name>, \"action\": "
    "\"drop_column\"|\"impute_missing\"|\"cast_type\"|\"encode\"|\"handle_outliers\", "
    "\"reason\": <short>}]}. Base every proposal on the stats given (missing_pct, "
    "cardinality, is_constant, duplicate_of, corr_to_target, mutual_info, "
    "leakage_suspect). Do NOT propose dropping a column that carries signal. "
    "Return an empty list when the data is clean."
)


def _llm_review(profile: dict) -> list[dict]:
    payload = {
        "target": profile["target"],
        "task": profile["task"],
        "columns": profile["columns"],
    }
    raw = complete_json(_REVIEW_SYSTEM, json.dumps(payload, default=str))
    return raw.get("proposals", [])


# ── nodes ────────────────────────────────────────────────────────────────────

def profile_node(state: dict) -> dict:
    df = store.get(state["run_id"])
    prof = compute_profile(df, state["target"])
    return {"profile": prof, "iterations": state.get("iterations", 0) + 1}


def review_node(state: dict) -> dict:
    return {"proposals": _llm_review(state["profile"])}


def gate_node(state: dict) -> dict:
    resolved = set(state.get("resolved_keep", []))
    # Don't re-propose anything the user already decided to keep — no nagging loop.
    proposals = [p for p in state.get("proposals", []) if p.get("col") not in resolved]
    approved, rejected = gate(proposals, state["profile"])
    if rejected:
        logger.info(f"gate rejected: {[(p['col'], p['gate_reason']) for p in rejected]}")
    return {"approved": approved, "rejected": rejected}


def route_after_gate(state: dict) -> str:
    if state.get("iterations", 0) >= MAX_ITERATIONS:
        return "end"
    approved = state.get("approved", [])
    if not approved:
        return "end"
    # Destructive actions need explicit user confirmation.
    if any(p["action"] == "drop_column" for p in approved):
        return "ask_user"
    return "apply"


def ask_user_node(state: dict) -> dict:
    drops = [p for p in state.get("approved", []) if p["action"] == "drop_column"]
    # Pauses the graph; the endpoint resumes it with {col: "drop"|"keep"}.
    answer = interrupt({
        "message": "Confirm column drops (statistical evidence attached).",
        "proposals": drops,
    })
    return {"user_decisions": answer or {}}


def apply_node(state: dict) -> dict:
    df = store.get(state["run_id"]).copy()
    applied = list(state.get("applied", []))
    resolved_keep = list(state.get("resolved_keep", []))
    decisions = state.get("user_decisions", {})

    for p in state.get("approved", []):
        col, action = p["col"], p["action"]
        if action == "drop_column":
            # Safe default: only drop when the user explicitly said so.
            if decisions.get(col) == "drop" and col in df.columns:
                df = df.drop(columns=[col])
                applied.append({**p, "result": "dropped"})
            else:
                applied.append({**p, "result": "kept_by_user"})
                resolved_keep.append(col)   # never re-propose a kept column
        elif action == "impute_missing" and col in df.columns:
            fill = df[col].median() if pd.api.types.is_numeric_dtype(df[col]) else _mode(df[col])
            df[col] = df[col].fillna(fill)
            applied.append({**p, "result": "imputed"})
        else:
            applied.append({**p, "result": "noted"})

    # Persist the mutated frame out-of-band; clear the working set so the next
    # loop re-derives from a fresh profile.
    store.put(state["run_id"], df)
    return {
        "applied": applied, "resolved_keep": resolved_keep,
        "user_decisions": {}, "approved": [], "proposals": [],
    }


def _mode(s: pd.Series):
    m = s.mode(dropna=True)
    return m.iloc[0] if len(m) else 0
