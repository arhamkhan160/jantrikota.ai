"""
tests/test_stats_gate.py
The core safety claim in tests: the gate refuses to drop a column that carries
signal, and only allows drops the statistics justify.
"""

from validation.gate import gate


def _profile(**cols):
    return {"columns": cols}


def _col(is_constant=False, duplicate_of=None, leakage_suspect=False, mutual_info=0.3):
    return {
        "is_constant": is_constant,
        "duplicate_of": duplicate_of,
        "leakage_suspect": leakage_suspect,
        "mutual_info": mutual_info,
    }


def test_rejects_dropping_high_value_column():
    prof = _profile(age=_col(mutual_info=0.5))
    approved, rejected = gate([{"col": "age", "action": "drop_column"}], prof)
    assert not approved
    assert rejected and rejected[0]["col"] == "age"


def test_allows_dropping_constant():
    prof = _profile(flag=_col(is_constant=True, mutual_info=0.0))
    approved, rejected = gate([{"col": "flag", "action": "drop_column"}], prof)
    assert approved and approved[0]["col"] == "flag"
    assert not rejected


def test_allows_dropping_leakage():
    prof = _profile(id_leak=_col(leakage_suspect=True, mutual_info=0.9))
    approved, _ = gate([{"col": "id_leak", "action": "drop_column"}], prof)
    assert approved and approved[0]["col"] == "id_leak"


def test_allows_dropping_duplicate():
    prof = _profile(copy=_col(duplicate_of="orig"))
    approved, _ = gate([{"col": "copy", "action": "drop_column"}], prof)
    assert approved and approved[0]["col"] == "copy"


def test_allows_low_signal_drop():
    prof = _profile(noise=_col(mutual_info=0.0001))
    approved, _ = gate([{"col": "noise", "action": "drop_column"}], prof)
    assert approved


def test_non_destructive_passes():
    prof = _profile(a=_col(mutual_info=0.3))
    approved, rejected = gate([{"col": "a", "action": "impute_missing"}], prof)
    assert approved and not rejected


def test_unknown_column_rejected():
    approved, rejected = gate([{"col": "ghost", "action": "drop_column"}], _profile(a=_col()))
    assert not approved and rejected
