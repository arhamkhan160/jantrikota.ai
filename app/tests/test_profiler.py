"""
tests/test_profiler.py
The safety rail. Plant known-bad columns; assert the profiler flags exactly them.
If these break, the whole "no dropping on vibes" guarantee is void.
"""

import numpy as np
import pandas as pd

from validation.profiler import profile


def _frame(n=300):
    rng = np.random.default_rng(0)
    signal = rng.normal(0, 1, n)
    target = (signal + rng.normal(0, 0.1, n) > 0).astype(int)  # binary classification
    return pd.DataFrame({
        "good_feature": signal,                    # predictive, not leaky
        "noise": rng.normal(0, 1, n),              # useless but harmless
        "constant": np.ones(n),                    # zero-variance
        "leaky_proxy": target,                     # == target -> leakage
        "target": target,
    })


def test_flags_leakage():
    p = profile(_frame(), "target")["columns"]
    assert p["leaky_proxy"]["leakage_suspect"] is True


def test_flags_constant():
    p = profile(_frame(), "target")["columns"]
    assert p["constant"]["is_constant"] is True


def test_does_not_flag_good_feature():
    # A genuinely predictive-but-not-leaky feature must NOT be marked leakage.
    p = profile(_frame(), "target")["columns"]
    assert p["good_feature"]["leakage_suspect"] is False
    assert p["noise"]["leakage_suspect"] is False


def test_detects_duplicate():
    df = _frame()
    df["good_copy"] = df["good_feature"]
    p = profile(df, "target")["columns"]
    assert p["good_copy"]["duplicate_of"] == "good_feature"


def test_task_inference():
    assert profile(_frame(), "target")["task"] == "classification"
