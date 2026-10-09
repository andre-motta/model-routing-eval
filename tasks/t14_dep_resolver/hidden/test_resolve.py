import time

import pytest

from resolver import resolve, ResolutionError, Version, Constraint

INDEX = {
    "app": {"1.0": ["web>=2", "db"]},
    "web": {"1.0": [], "2.0": ["json<3"], "2.1": ["json>=3"]},
    "json": {"2.0": [], "3.0": []},
    "db": {"1.0": ["json<3"]},
}


def test_versions_and_constraints():
    assert Version("1.10") > Version("1.9") and Version("1.0") == Version("1") and str(Version("1.0")) == "1.0"
    assert len({Version("1.0"), Version("1")}) == 1
    c = Constraint.parse("json>=2,<3")
    assert c.name == "json" and c.allows(Version("2.5")) and not c.allows(Version("3.0")) and not c.allows(Version("1.9"))
    assert Constraint.parse("db").allows(Version("0.1"))
    assert not Constraint.parse("x!=1.0").allows(Version("1"))


def test_backtracks_to_consistent_solution():
    # web 2.1 is highest but forces json>=3, which conflicts with db -> json<3. Must pick web 2.0.
    assert resolve(["app"], INDEX) == {"app": "1.0", "web": "2.0", "json": "2.0", "db": "1.0"}


def test_preference_order_is_by_package_name():
    index = {"a": {"1": ["c<2"], "2": ["c>=2"]}, "b": {"1": ["c<2"], "2": ["c>=2"]}, "c": {"1": [], "2": []}}
    # a gets priority: a=2 forces c=2, then b must be 2.
    assert resolve(["a", "b"], index) == {"a": "2", "b": "2", "c": "2"}
    index2 = {"a": {"1": ["c<2"], "2": ["c<2"]}, "b": {"1": [], "2": ["c>=2"]}, "c": {"1": [], "2": []}}
    assert resolve(["a", "b"], index2) == {"a": "2", "b": "1", "c": "1"}


def test_cycle_and_unreachable():
    index = {"a": {"1": ["b"]}, "b": {"1": ["a"]}, "z": {"9": []}}
    assert resolve(["a"], index) == {"a": "1", "b": "1"}


def test_no_solution_names_package():
    index = {"a": {"1": ["b<1"]}, "b": {"1": [], "2": []}}
    with pytest.raises(ResolutionError) as e:
        resolve(["a"], index)
    assert "b" in str(e.value)
    with pytest.raises(ResolutionError):
        resolve(["nope"], {})


def test_large_index_needs_pruning():
    # 12 packages, each with 30 versions; only the lowest version of each depends on nothing problematic.
    # Every version v of p_i (i < 11) requires p_{i+1} with the same version string, and p_11 only has "0".
    # Highest-first naive enumeration without propagation explores 30^11 combos.
    index = {}
    for i in range(12):
        name = f"p{i:02d}"
        versions = {}
        for v in range(30):
            reqs = [f"p{i + 1:02d}=={v}"] if i < 11 else []
            versions[str(v)] = reqs
        index[name] = versions
    index["p11"] = {"0": []}
    t0 = time.perf_counter()
    sol = resolve(["p00"], index)
    assert sol == {f"p{i:02d}": "0" for i in range(12)}
    assert time.perf_counter() - t0 < 60
