"""
tests/test_spec_builder.py
NLP layer: query + columns -> TaskSpec. LLM is mocked (no key needed).
Checks the target-resolution logic — the part that must not drop/guess wrong.
"""

from unittest.mock import patch

from core.constants import TaskType
from services.spec_builder import build_spec

COLUMNS = ["area", "bedrooms", "sale_price"]


def _mock(**ret):
    return patch("services.spec_builder.complete_json", return_value=ret)


def test_exact_target_resolves():
    with _mock(task="regression", target="sale_price", metric="rmse"):
        spec = build_spec("predict the sale price", COLUMNS, dataset_id="d1")
    assert spec.task == TaskType.REGRESSION
    assert spec.target == "sale_price"
    assert spec.metric == "rmse"
    assert not spec.ambiguous


def test_close_target_is_salvaged():
    # LLM returns a near-miss (case/format); resolver maps it to the real column.
    with _mock(task="regression", target="Sale_Price", metric="rmse"):
        spec = build_spec("predict price", COLUMNS, dataset_id="d1")
    assert spec.target == "sale_price"
    assert not spec.ambiguous


def test_unknown_target_is_flagged_ambiguous():
    # LLM invents a column that doesn't exist -> must NOT silently pass through.
    with _mock(task="regression", target="cost", metric="rmse"):
        spec = build_spec("predict the cost", COLUMNS, dataset_id="d1")
    assert spec.ambiguous
    assert spec.target == "cost"
    assert spec.candidates  # non-empty options for the user


def test_metric_defaults_when_omitted():
    with _mock(task="classification", target="bedrooms"):
        spec = build_spec("classify by bedrooms", COLUMNS, dataset_id="d1")
    assert spec.metric == "accuracy"
