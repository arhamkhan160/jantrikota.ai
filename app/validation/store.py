"""
validation/store.py
In-memory working DataFrames, keyed by run_id.

LangGraph checkpoints state via msgpack, which can't serialize a DataFrame, so
the live frame lives here instead of in graph state. State keeps only JSON-safe
data (profile, proposals, applied, ...).

# ponytail: in-memory dict, single-worker. Move to a shared/disk store for multi-worker.
"""

import pandas as pd

_WORKING: dict[str, pd.DataFrame] = {}


def put(run_id: str, df: pd.DataFrame) -> None:
    _WORKING[run_id] = df


def get(run_id: str) -> pd.DataFrame:
    if run_id not in _WORKING:
        raise KeyError(f"no working dataframe for run '{run_id}'")
    return _WORKING[run_id]


def drop(run_id: str) -> None:
    _WORKING.pop(run_id, None)
