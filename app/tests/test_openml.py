"""
tests/test_openml.py
OpenML integration, offline. `openml`, embeddings, and the LLM are all mocked.
"""

from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pandas as pd

import integrations.openml as om


def _index():
    return pd.DataFrame({
        "did": [1, 2, 61],
        "name": ["iris", "wine", "iris-variant"],
        "NumberOfInstances": [150, 178, 120],
        "NumberOfFeatures": [5, 14, 5],
    })


def test_search_semantic_ranks_by_similarity():
    # Query embeds like 'iris'; 'wine' is orthogonal -> iris-family ranks top.
    def fake_embed(texts):
        vecs = {"iris": [1.0, 0.0], "wine": [0.0, 1.0], "iris-variant": [0.9, 0.1]}
        return [[1.0, 0.0]] + [vecs[t] for t in texts[1:]]

    with patch("integrations.openml._list", return_value=_index()), \
         patch("integrations.openml.embed", side_effect=fake_embed):
        hits = om.search("iris", limit=10)

    assert hits[0]["name"] == "iris"
    assert hits[0]["confidence"] >= hits[1]["confidence"]
    assert {h["name"] for h in hits} == {"iris", "iris-variant"}  # 'wine' filtered out by name


def test_search_falls_back_to_lexical_without_embeddings():
    with patch("integrations.openml._list", return_value=_index()), \
         patch("integrations.openml.embed", side_effect=RuntimeError("no key")):
        hits = om.search("iris", limit=10)

    assert hits and hits[0]["name"] == "iris"
    assert all("confidence" in h for h in hits)


def test_search_respects_limit():
    idx = pd.DataFrame({
        "did": [1, 2, 3], "name": ["data_a", "data_b", "data_c"],
        "NumberOfInstances": [10, 20, 30], "NumberOfFeatures": [2, 3, 4],
    })
    with patch("integrations.openml._list", return_value=idx), \
         patch("integrations.openml.embed", side_effect=RuntimeError("no key")):
        assert len(om.search("data", limit=2)) == 2


def test_detail_reads_columns_from_metadata_only():
    ds = MagicMock()
    ds.name = "iris"
    ds.description = "Classic flower dataset."
    ds.default_target_attribute = "class"
    ds.features = {
        0: SimpleNamespace(name="sepal_length", data_type="numeric", number_missing_values=0, nominal_values=None),
        1: SimpleNamespace(name="class", data_type="nominal", number_missing_values=0, nominal_values=["a", "b", "c"]),
    }
    with patch("integrations.openml._get_dataset", return_value=ds) as gd:
        d = om.detail(61)

    # metadata only — must NOT download the data
    gd.assert_called_once_with(61, download_data=False)
    assert d["target"] == "class"
    names = [c["name"] for c in d["columns"]]
    assert names == ["sepal_length", "class"]
    cls = next(c for c in d["columns"] if c["name"] == "class")
    assert cls["n_distinct"] == 3


def test_fetch_builds_frame_with_target():
    ds = MagicMock()
    ds.default_target_attribute = "class"
    ds.get_data.return_value = (
        pd.DataFrame({"a": [1, 2], "b": [3, 4]}),
        pd.Series([0, 1], name="class"),
        None, None,
    )
    with patch("integrations.openml._get_dataset", return_value=ds):
        df, target = om.fetch(61)

    assert target == "class"
    assert list(df.columns) == ["a", "b", "class"]
