"""
agent/state.py
State for the supervisor agent. msgpack-safe (no DataFrame — datasets live on
disk by dataset_id), so it checkpoints cleanly across human-in-the-loop pauses.
"""

from typing import TypedDict


class AgentState(TypedDict, total=False):
    query: str
    sources: list[str]
    candidates: list[dict]        # search hits
    chosen_ref: str               # dataset the user picked
    dataset_id: str               # after fetch + save
    suggested_target: str | None  # target from the source (OpenML labels it)
    target: str
    task: str
    metric: str
    data_flags: list[str]         # leakage suspects surfaced in the report
    job_id: str
    report: dict
