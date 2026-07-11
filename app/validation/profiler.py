"""
validation/profiler.py
Pure statistical profile of a dataset. NO LLM.

This is the safety rail for the whole validation agent (M4): the LLM only ever
*proposes* changes off this profile, and the stats_gate rejects any proposal the
numbers here don't support. If the profiler is wrong, the guarantee is wrong —
so it is built and tested before any LLM touches the data.

profile(df, target) -> {
    n_rows, n_cols, target, task,
    columns: { col: {dtype, missing_pct, cardinality, is_constant,
                     duplicate_of, corr_to_target, mutual_info, leakage_suspect} }
}
"""

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression

from core.constants import TaskType
from core.logger import get_logger

logger = get_logger(__name__)

LEAKAGE_CORR = 0.98   # |pearson| at/above this vs the target = suspect leakage


def infer_task(y: pd.Series) -> TaskType:
    """Low-cardinality / non-numeric target -> classification, else regression."""
    if y.dtype == object or str(y.dtype) in ("category", "bool"):
        return TaskType.CLASSIFICATION
    return TaskType.CLASSIFICATION if y.nunique(dropna=True) <= 20 else TaskType.REGRESSION


def _is_numeric(s: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s)


def _to_numeric_frame(X: pd.DataFrame) -> pd.DataFrame:
    """Numeric copy for mutual-info: factorize categoricals, impute NaN. Never mutates X."""
    out = pd.DataFrame(index=X.index)
    for c in X.columns:
        s = X[c]
        if _is_numeric(s):
            out[c] = pd.to_numeric(s, errors="coerce")
        else:
            out[c] = pd.factorize(s)[0].astype(float)
    return out.fillna(out.median(numeric_only=True)).fillna(0.0)


def _perfect_predictor(feature: pd.Series, y: pd.Series) -> bool:
    """Classification leakage: every feature value maps to exactly one target value.

    Only meaningful for categorical-like features — a continuous/near-unique column
    trivially has one row per value, so require values to cover many rows
    (cardinality <= half the rows) before trusting the signal.
    """
    card = feature.nunique(dropna=True)
    if card <= 1 or card > len(feature) * 0.5:
        return False
    grouped = y.groupby(feature, dropna=False).nunique(dropna=False)
    return bool((grouped <= 1).all())


def profile(df: pd.DataFrame, target: str) -> dict:
    if target not in df.columns:
        raise ValueError(f"target '{target}' not in columns")

    y = df[target]
    X = df.drop(columns=[target])
    task = infer_task(y)
    n_rows = len(df)

    # Mutual information on a cleaned numeric copy.
    mi_map: dict[str, float] = {}
    if len(X.columns) and n_rows > 1:
        Xn = _to_numeric_frame(X)
        if task == TaskType.CLASSIFICATION:
            yn = pd.factorize(y)[0]
            mi_vals = mutual_info_classif(Xn, yn, random_state=0)
        else:
            yn = pd.to_numeric(y, errors="coerce")
            yn = yn.fillna(yn.median()).to_numpy()
            mi_vals = mutual_info_regression(Xn, yn, random_state=0)
        mi_map = {c: float(v) for c, v in zip(Xn.columns, mi_vals)}

    # Pearson corr to target only when both sides are genuinely numeric.
    target_numeric = _is_numeric(y)
    y_num = pd.to_numeric(y, errors="coerce") if target_numeric else None

    # Precompute column signatures for duplicate detection.
    seen: dict[tuple, str] = {}
    columns: dict[str, dict] = {}

    for c in X.columns:
        s = X[c]
        cardinality = int(s.nunique(dropna=True))
        is_constant = cardinality <= 1

        corr = None
        if target_numeric and _is_numeric(s):
            pair = pd.concat([pd.to_numeric(s, errors="coerce"), y_num], axis=1).dropna()
            if len(pair) > 1 and pair.iloc[:, 0].std() > 0 and pair.iloc[:, 1].std() > 0:
                corr = float(pair.iloc[:, 0].corr(pair.iloc[:, 1]))

        # duplicate-of another feature
        sig = tuple(pd.factorize(s.fillna("__na__") if s.dtype == object else s)[0])
        duplicate_of = seen.get(sig)
        if duplicate_of is None:
            seen[sig] = c

        # duplicate-of target
        dup_of_target = s.equals(y) or (len(s) == len(y) and (s.astype(str).values == y.astype(str).values).all())

        leakage = bool(
            dup_of_target
            or (corr is not None and abs(corr) >= LEAKAGE_CORR)
            or (task == TaskType.CLASSIFICATION and _perfect_predictor(s, y))
        )

        columns[c] = {
            "dtype": str(s.dtype),
            "missing_pct": float(s.isna().mean() * 100.0),
            "cardinality": cardinality,
            "is_constant": is_constant,
            "duplicate_of": duplicate_of,
            "corr_to_target": corr,
            "mutual_info": mi_map.get(c),
            "leakage_suspect": leakage,
        }

    return {
        "n_rows": n_rows,
        "n_cols": len(df.columns),
        "target": target,
        "task": task.value,
        "columns": columns,
    }
