"""
tests/test_llm.py
Round-robin + failover across multiple LLM keys. No real network — fake clients.
"""

import itertools

import integrations.llm as llm


class _Resp:
    def __init__(self, content):
        msg = type("M", (), {"content": content})()
        self.choices = [type("C", (), {"message": msg})()]


class _Completions:
    def __init__(self, name, fail, log):
        self.name, self.fail, self.log = name, fail, log

    def create(self, **kw):
        self.log.append(self.name)
        if self.fail:
            raise RuntimeError("429 rate limited")
        return _Resp('{"key": "%s"}' % self.name)


class _Client:
    def __init__(self, name, fail, log):
        self.chat = type("Chat", (), {"completions": _Completions(name, fail, log)})()


def _install(monkeypatch, clients):
    monkeypatch.setattr(llm, "_pool", clients)
    monkeypatch.setattr(llm, "_rr", itertools.count())


def test_round_robin_cycles_keys(monkeypatch):
    log = []
    _install(monkeypatch, [_Client("k1", False, log), _Client("k2", False, log)])

    r1 = llm.complete_json("s", "u")
    r2 = llm.complete_json("s", "u")
    r3 = llm.complete_json("s", "u")

    assert (r1["key"], r2["key"], r3["key"]) == ("k1", "k2", "k1")
    assert log == ["k1", "k2", "k1"]   # each call used exactly one key, rotating


def test_failover_to_next_key(monkeypatch):
    log = []
    _install(monkeypatch, [_Client("bad", True, log), _Client("good", False, log)])

    result = llm.complete_json("s", "u")   # starts at 'bad' -> fails -> 'good'
    assert result["key"] == "good"
    assert log == ["bad", "good"]


def test_all_keys_fail_raises(monkeypatch):
    log = []
    _install(monkeypatch, [_Client("a", True, log), _Client("b", True, log)])

    try:
        llm.complete_json("s", "u")
        assert False, "expected failure when all keys fail"
    except RuntimeError:
        pass
