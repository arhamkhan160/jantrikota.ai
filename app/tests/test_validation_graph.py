"""
tests/test_validation_graph.py
End-to-end agent loop with a MOCKED LLM (no key). Exercises graph wiring,
the human-in-the-loop interrupt, resume, and termination.
"""

from unittest.mock import patch

import pandas as pd
from langgraph.types import Command

from validation import store
from validation.graph import build_graph


def _df():
    # 'const' is zero-variance (droppable); 'a' carries signal; target is binary.
    return pd.DataFrame({
        "const": [7, 7, 7, 7, 7, 7],
        "a": [1, 2, 3, 4, 5, 6],
        "target": [0, 0, 1, 1, 0, 1],
    })


def _run(run_id: str):
    store.put(run_id, _df())
    return {"run_id": run_id, "target": "target", "applied": [], "iterations": 0}, \
           {"configurable": {"thread_id": run_id}}


def test_terminates_clean_when_no_proposals():
    g = build_graph()
    inputs, cfg = _run("clean-1")
    with patch("validation.nodes._llm_review", return_value=[]):
        res = g.invoke(inputs, cfg)
    assert "__interrupt__" not in res
    assert res["applied"] == []


def test_interrupts_then_drops_on_user_confirm():
    g = build_graph()
    inputs, cfg = _run("drop-1")
    proposal = [{"col": "const", "action": "drop_column", "reason": "constant"}]

    with patch("validation.nodes._llm_review", return_value=proposal):
        res = g.invoke(inputs, cfg)
        # Paused for confirmation — the gate approved (constant) but a drop needs the user.
        assert "__interrupt__" in res
        # The question must carry the LLM reason, gate reason, and real stats evidence.
        pending = res["__interrupt__"][0].value["proposals"][0]
        assert pending["reason"] == "constant"
        assert "gate_reason" in pending
        assert pending["evidence"]["is_constant"] is True

        # Second call re-proposes 'const', but it's gone after apply -> gate rejects -> ends.
        res2 = g.invoke(Command(resume={"const": "drop"}), cfg)

    assert "__interrupt__" not in res2
    dropped = [a for a in res2["applied"] if a["col"] == "const" and a["result"] == "dropped"]
    assert dropped, "constant column should have been dropped after user confirmed"
    assert "const" not in store.get("drop-1").columns


def test_user_can_reject_drop():
    g = build_graph()
    inputs, cfg = _run("keep-1")
    proposal = [{"col": "const", "action": "drop_column", "reason": "constant"}]

    with patch("validation.nodes._llm_review", return_value=proposal):
        g.invoke(inputs, cfg)
        res2 = g.invoke(Command(resume={"const": "keep"}), cfg)

    assert "__interrupt__" not in res2, "keeping a column must not re-nag the user"
    kept = [a for a in res2["applied"] if a["col"] == "const" and a["result"] == "kept_by_user"]
    assert kept, "user 'keep' must prevent the drop"
    assert "const" in store.get("keep-1").columns
