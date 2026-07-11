"""
validation/state.py
State that flows through the LangGraph validation agent.

Checkpointed via MemorySaver (msgpack), so state stays JSON-safe: the live
DataFrame is held out-of-band in validation/store.py, referenced here by run_id.
`applied` is the audit trail — every mutation with its reason and who approved it.
"""

from typing import TypedDict


class ValidationState(TypedDict, total=False):
    run_id: str                   # key into validation/store.py for the live DataFrame
    target: str
    profile: dict                 # latest stats snapshot (validation/profiler.py)
    proposals: list[dict]         # raw LLM suggestions
    approved: list[dict]          # survived the stats gate
    rejected: list[dict]          # gate said the numbers don't support it
    user_decisions: dict          # {col: "drop"|"keep"} from the human-in-the-loop
    resolved_keep: list[str]      # columns the user chose to keep — don't re-propose
    applied: list[dict]           # audit trail of actual mutations
    iterations: int               # loop guard
