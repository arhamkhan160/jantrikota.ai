"""
tests/test_sources.py
Multi-source registry + HF/Kaggle/URL sources, offline (all network mocked).
"""

import pytest

from integrations import sources_registry as reg


def test_ref_split():
    assert reg._split("openml:61") == ("openml", "61")
    # URLs contain ':' — split only once
    assert reg._split("url:https://x.com/a.csv") == ("url", "https://x.com/a.csv")
    with pytest.raises(ValueError):
        reg._split("no-colon")
    with pytest.raises(ValueError):
        reg._split("bogus:1")   # unknown source


def test_registry_fetch_dispatches(monkeypatch):
    seen = {}
    monkeypatch.setattr(reg._SOURCES["url"], "fetch", lambda nid: (seen.setdefault("nid", nid), None))
    df, target = reg.fetch("url:http://x/a.csv")
    assert seen["nid"] == "http://x/a.csv"
    assert target is None


def test_registry_search_skips_broken_source(monkeypatch):
    def boom(q, limit):
        raise RuntimeError("no auth")
    monkeypatch.setattr(reg._SOURCES["kaggle"], "search", boom)
    monkeypatch.setattr(reg._SOURCES["openml"], "search",
                        lambda q, limit: [{"ref": "openml:1", "source": "openml", "name": "iris"}])
    hits = reg.search("iris", sources=["openml", "kaggle"])   # kaggle fails, openml survives
    assert [h["ref"] for h in hits] == ["openml:1"]


def test_url_source_reads_csv(monkeypatch):
    import pandas as pd
    from integrations import url_source
    monkeypatch.setattr(pd, "read_csv", lambda u: pd.DataFrame({"a": [1, 2]}))
    df, target = url_source.fetch("http://x/data.csv")
    assert list(df.columns) == ["a"] and target is None


def test_url_source_reads_html_table(monkeypatch):
    import pandas as pd
    from integrations import url_source
    monkeypatch.setattr(pd, "read_html", lambda u: [pd.DataFrame({"b": [1, 2, 3]})])
    df, _ = url_source.fetch("http://x/page.html")   # no data extension -> HTML tables
    assert list(df.columns) == ["b"]


def test_hf_search(monkeypatch):
    import huggingface_hub
    from integrations import hf

    class _D:
        def __init__(self, i): self.id = i

    class _API:
        def list_datasets(self, search, limit): return [_D("imdb"), _D("glue")]

    monkeypatch.setattr(huggingface_hub, "HfApi", lambda: _API())
    hits = hf.search("imdb", 5)
    assert hits[0]["ref"] == "hf:imdb" and hits[0]["source"] == "hf"


def test_kaggle_search(monkeypatch):
    from integrations import kaggle as kag

    class _DS:
        def __init__(self, r): self.ref = r

    class _API:
        def dataset_list(self, search): return [_DS("owner/a"), _DS("owner/b")]

    monkeypatch.setattr(kag, "_api", lambda: _API())
    hits = kag.search("x", 5)
    assert hits[0]["ref"] == "kaggle:owner/a" and hits[0]["source"] == "kaggle"
