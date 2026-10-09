import time

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
    assert Constraint.parse("db").allows(Version("0.1"))
    assert not Constraint.parse("db!=1").allows(Version("1.0"))


def test_example():
    assert resolve(["app"], INDEX) == {"app": "1.0", "web": "2.0", "json": "2.0", "db": "1.0"}


def test_unreachable_excluded():
    assert set(resolve(["json"], INDEX)) == {"json"}


def test_cycle():
    idx = {"a": {"1": ["b"]}, "b": {"1": ["a"]}}
    assert resolve(["a"], idx) == {"a": "1", "b": "1"}


def test_error_names_leaf():
    idx = {"a": {"1": ["b<1"]}, "b": {"1": [], "2": []}}
    with pytest.raises(ResolutionError, match="b"):
        resolve(["a"], idx)


def test_backtrack():
    idx = {"a": {"1": ["b==1"], "2": ["b==3"]}, "b": {"1": [], "2": []}}
    assert resolve(["a"], idx) == {"a": "1", "b": "1"}


def test_missing_root():
    with pytest.raises(ResolutionError, match="zzz"):
        resolve(["zzz"], INDEX)


def test_large():
    idx = {}
    n = 40
    for i in range(n):
        idx[f"p{i:02d}"] = {
            f"{v}.0": ([f"p{i+1:02d}>={v}"] if i + 1 < n else []) + ([f"p{(i+2)%n:02d}!=9"] if i + 2 < n else [])
            for v in range(8)
        }
    # unsatisfiable tail forces deep backtracking
    idx["p39"] = {"0.0": []}
    t = time.time()
    try:
        resolve(["p00"], idx)
    except ResolutionError:
        pass
    assert time.time() - t < 20
