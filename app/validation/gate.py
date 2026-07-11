"""
validation/gate.py
The safety rail, as pure functions (no LLM, no graph) so it can be unit-tested
in isolation.

Rule: the LLM may *propose* anything; a destructive action (drop_column) is only
allowed if the STATISTICS support it — the column is constant, a duplicate, a
leakage suspect, or carries near-zero signal. A column with real predictive value
is never dropped on the LLM's say-so. Non-destructive actions pass through.
"""

LOW_MI = 0.01          # mutual_info below this = effectively no signal
DESTRUCTIVE = {"drop_column"}
NON_DESTRUCTIVE = {
    "impute_missing", "cast_type", "encode",
    "handle_outliers", "flag_leakage", "flag_confounder",
}


def is_supported(proposal: dict, profile: dict) -> tuple[bool, str]:
    """(allowed, reason) — does the stats profile support this proposal?"""
    action = proposal.get("action")
    col = proposal.get("col")
    stats = profile.get("columns", {}).get(col)

    if stats is None:
        return False, f"unknown column '{col}'"

    if action == "drop_column":
        if stats.get("is_constant"):
            return True, "constant column"
        if stats.get("duplicate_of"):
            return True, f"duplicate of '{stats['duplicate_of']}'"
        if stats.get("leakage_suspect"):
            return True, "leakage suspect"
        mi = stats.get("mutual_info")
        if mi is not None and mi < LOW_MI:
            return True, f"near-zero mutual_info={mi:.4f}"
        return False, "column carries signal — refusing to drop on LLM judgment alone"

    if action in NON_DESTRUCTIVE:
        return True, "non-destructive"

    return False, f"unknown action '{action}'"


def gate(proposals: list[dict], profile: dict) -> tuple[list[dict], list[dict]]:
    """Split proposals into (approved, rejected), annotating each with gate_reason."""
    approved, rejected = [], []
    for p in proposals:
        ok, reason = is_supported(p, profile)
        entry = {**p, "gate_reason": reason}
        (approved if ok else rejected).append(entry)
    return approved, rejected
