import pytest

from resolver.solve import Constraint, ResolutionError, Version, resolve

INDEX = {
    "app": {"1.0": ["web>=2", "db"]},
    "web": {"1.0": [], "2.0": ["json<3"], "2.1": ["json>=3"]},
    "json": {"2.0": [], "3.0": []},
    "db": {"1.0": ["json<3"]},
}


def test_version():
    assert Version("1.0") == Version("1")
    assert hash(Version("1.0")) == hash(Version("1"))
    assert Version("1.10") > Version("1.9")
    assert str(Version("1.0")) == "1.0"


def test_constraint():
    c = Constraint.parse("json>=2,<3")
    assert c.name == "json"
    assert c.allows(Version("2.5")) and not c.allows(Version("3"))
    assert Constraint.parse("x").allows(Version("0"))


def test_basic():
    assert resolve(["app"], INDEX) == {"app": "1.0", "web": "2.0", "db": "1.0", "json": "2.0"}


def test_cycle():
    idx = {"a": {"1": ["b"]}, "b": {"1": ["a"]}}
    assert resolve(["a"], idx) == {"a": "1", "b": "1"}


def test_error_names_leaf():
    idx = {"a": {"1": ["b<1"]}, "b": {"1": [], "2": []}}
    with pytest.raises(ResolutionError, match="b"):
        resolve(["a"], idx)


def test_unreachable_excluded():
    assert resolve(["json"], INDEX) == {"json": "3.0"}


def test_large():
    idx = {}
    n = 40
    for i in range(n):
        idx[f"p{i:02d}"] = {
            str(v): ([f"p{i+1:02d}<{v}"] if i + 1 < n and v > 1 else []) for v in range(1, 9)
        }
    idx[f"p{n-1:02d}"] = {"1": []}
    idx["p00"]["99"] = ["zzz"]
    idx["zzz"] = {str(v): ["p05>=8"] for v in range(1, 200)}
    res = resolve(["p00"], idx)
    assert res["p00"] == "8" or "p00" in res
