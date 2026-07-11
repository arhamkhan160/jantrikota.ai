"""
tests/test_openml.py
OpenML integration, offline. `openml` is mocked — no network.
"""

from unittest.mock import patch, MagicMock

import pandas as pd

import integrations.openml as om


def test_search_filters_by_name():
    index = pd.DataFrame({
        "did": [1, 2, 61],
        "name": ["iris", "wine", "iris-variant"],
        "NumberOfInstances": [150, 178, 120],
        "NumberOfFeatures": [5, 14, 5],
    })
    with patch("integrations.openml._list", return_value=index):
        hits = om.search("iris", limit=10)

    names = {h["name"] for h in hits}
    assert names == {"iris", "iris-variant"}
    first = next(h for h in hits if h["name"] == "iris")
    assert first["openml_id"] == 1 and first["rows"] == 150


def test_search_respects_limit():
    index = pd.DataFrame({
        "did": [1, 2, 3],
        "name": ["data_a", "data_b", "data_c"],
        "NumberOfInstances": [10, 20, 30],
        "NumberOfFeatures": [2, 3, 4],
    })
    with patch("integrations.openml._list", return_value=index):
        hits = om.search("data", limit=2)
    assert len(hits) == 2


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
    assert df["class"].tolist() == [0, 1]
