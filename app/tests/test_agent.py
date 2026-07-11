"""
tests/test_agent.py
Supervisor agent orchestration + human-in-the-loop, offline.
registry.search/fetch and the trainer are mocked; save/load/profile/infer are real.
"""

from unittest.mock import patch

import pandas as pd
from langgraph.types import Command

from agent.graph import build_graph
from schemas.query import TaskSpec

_TRAIN_RESULT = {
    "best_model": "rf", "best_metrics": {"accuracy": 0.9},
    "all_results": [], "model_path": "/tmp/x.joblib",
}


def _df():
    return pd.DataFrame({"a": [1, 2, 3, 4], "b": [5, 6, 7, 8], "target": [0, 1, 0, 1]})


def _start(g, thread, query="predict target", sources=("openml",)):
    return g.invoke({"query": query, "sources": list(sources)},
                    {"configurable": {"thread_id": thread}})


def test_no_datasets_ends_cleanly():
    g = build_graph()
    with patch("agent.nodes.registry.search", return_value=[]):
        res = _start(g, "n1")
    assert "__interrupt__" not in res
    assert res["report"]["status"] == "no_datasets"


def test_happy_path_labeled_target():
    g = build_graph()
    cfg = {"configurable": {"thread_id": "h1"}}
    cands = [{"ref": "openml:1", "source": "openml", "name": "iris"}]
    with patch("agent.nodes.registry.search", return_value=cands), \
         patch("agent.nodes.registry.fetch", return_value=(_df(), "target")), \
         patch("agent.nodes.train_model", return_value=_TRAIN_RESULT):
        res = g.invoke({"query": "predict target", "sources": ["openml"]}, cfg)
        assert res["__interrupt__"][0].value["type"] == "choose_dataset"
        res2 = g.invoke(Command(resume={"ref": "openml:1"}), cfg)

    assert "__interrupt__" not in res2
    r = res2["report"]
    assert r["status"] == "done" and r["best_model"] == "rf" and r["target"] == "target"


def test_confirms_target_when_source_unlabeled():
    g = build_graph()
    cfg = {"configurable": {"thread_id": "u1"}}
    cands = [{"ref": "hf:x", "source": "hf", "name": "x"}]
    ambiguous = TaskSpec(task="classification", target="unknown", metric="accuracy",
                         ambiguous=True, candidates=["a", "b", "target"])

    with patch("agent.nodes.registry.search", return_value=cands), \
         patch("agent.nodes.registry.fetch", return_value=(_df(), None)), \
         patch("agent.nodes.build_spec", return_value=ambiguous), \
         patch("agent.nodes.train_model", return_value=_TRAIN_RESULT):
        g.invoke({"query": "predict something", "sources": ["hf"]}, cfg)
        res2 = g.invoke(Command(resume={"ref": "hf:x"}), cfg)   # pick dataset
        assert res2["__interrupt__"][0].value["type"] == "confirm_target"
        res3 = g.invoke(Command(resume={"target": "target"}), cfg)  # confirm target

    assert "__interrupt__" not in res3
    assert res3["report"]["target"] == "target"
