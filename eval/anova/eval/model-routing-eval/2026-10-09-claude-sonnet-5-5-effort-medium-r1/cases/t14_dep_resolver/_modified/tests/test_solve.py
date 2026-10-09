import os
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "resolver"))
from solve import Constraint, ResolutionError, Version, resolve  # noqa: E402

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
    assert not Constraint.parse("x!=1").allows(Version("1.0"))


def test_example():
    assert resolve(["app"], INDEX) == {
        "app": "1.0", "web": "2.0", "json": "2.0", "db": "1.0"}


def test_cycle():
    idx = {"a": {"1": ["b"]}, "b": {"1": ["a"]}}
    assert resolve(["a"], idx) == {"a": "1", "b": "1"}


def test_backtrack():
    idx = {"a": {"1": ["b<2"], "2": ["b>=2"]}, "b": {"1": [], "2": ["c"]},
           "c": {"1": ["a<2"]}}
    assert resolve(["a"], idx) == {"a": "1", "b": "1"}


def test_error_names_leaf():
    idx = {"a": {"1": ["b<1"]}, "b": {"1": [], "2": []}}
    with pytest.raises(ResolutionError, match="b"):
        resolve(["a"], idx)


def test_unreachable_excluded():
    idx = {"a": {"1": []}, "z": {"1": []}}
    assert resolve(["a"], idx) == {"a": "1"}


def test_large():
    n = 40
    idx = {}
    for i in range(n):
        idx[f"p{i:02d}"] = {
            str(v): ([f"p{i+1:02d}>={v % 7}"] if i + 1 < n else [])
            for v in range(10)}
    idx[f"p{n-1:02d}"] = {str(v): [] for v in range(10)}
    idx["root"] = {"1": ["p00", "p39<3"]}
    t = time.time()
    res = resolve(["root"], idx)
    assert time.time() - t < 10
    assert res["p39"] == "2"
