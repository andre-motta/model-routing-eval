import time

import pytest

from resolver.solve import Constraint, ResolutionError, Version, resolve

SPEC_INDEX = {
    "app": {"1.0": ["web>=2", "db"]},
    "web": {"1.0": [], "2.0": ["json<3"], "2.1": ["json>=3"]},
    "json": {"2.0": [], "3.0": []},
    "db": {"1.0": ["json<3"]},
}


# Version and Constraint

def test_version_missing_components_are_zero():
    assert Version("1.0") == Version("1")
    assert hash(Version("1.0")) == hash(Version("1"))
    assert str(Version("1.0")) == "1.0"


def test_version_compares_numerically_component_wise():
    assert Version("1.10") > Version("1.9")
    assert Version("1.0.1") > Version("1")
    assert Version("2") > Version("1.99.99")
    assert sorted([Version("1.10"), Version("1.9"), Version("1.2")]) == [
        Version("1.2"), Version("1.9"), Version("1.10"),
    ]


@pytest.mark.parametrize("bad", ["", "1.", ".1", "a", "1.x", "1..2"])
def test_version_rejects_non_numeric(bad):
    with pytest.raises(ValueError):
        Version(bad)


def test_constraint_parse_name_and_bounds():
    c = Constraint.parse("json>=2,<3")
    assert c.name == "json"
    assert c.allows(Version("2"))
    assert c.allows(Version("2.5"))
    assert not c.allows(Version("3"))
    assert not c.allows(Version("1.9"))


def test_constraint_parse_bare_name_allows_everything():
    c = Constraint.parse("web")
    assert c.name == "web"
    assert c.allows(Version("0.1"))
    assert c.allows(Version("99"))


def test_constraint_parse_equality_and_inequality():
    assert Constraint.parse("db==1.0").allows(Version("1"))
    assert not Constraint.parse("db==1.0").allows(Version("1.1"))
    assert not Constraint.parse("db!=1.0").allows(Version("1.0"))


def test_constraint_parse_tolerates_spaces():
    c = Constraint.parse("json >= 2, < 3")
    assert c.name == "json"
    assert c.allows(Version("2.9"))
    assert not c.allows(Version("3"))


@pytest.mark.parametrize("bad", ["", ">=2", "web>>2", "web>=", "web>=2,,<3", "web=2"])
def test_constraint_parse_rejects_malformed(bad):
    with pytest.raises(ValueError):
        Constraint.parse(bad)


# resolve: spec behaviour

def test_spec_example_prefers_highest_consistent_versions():
    assert resolve(["app"], SPEC_INDEX) == {
        "app": "1.0", "db": "1.0", "json": "2.0", "web": "2.0",
    }


def test_highest_version_is_preferred_for_a_root():
    assert resolve(["web"], SPEC_INDEX) == {"web": "2.1", "json": "3.0"}


def test_empty_roots_resolve_to_nothing():
    assert resolve([], SPEC_INDEX) == {}


def test_unreachable_packages_are_excluded():
    index = {
        "a": {"1.0": []},
        "orphan": {"1.0": ["a"]},
    }
    assert resolve(["a"], index) == {"a": "1.0"}


def test_result_values_keep_the_original_version_string():
    index = {"a": {"1": [], "1.0.5": []}}
    assert resolve(["a>=1.0"], index) == {"a": "1.0.5"}


def test_cycle_is_tolerated():
    index = {
        "a": {"1.0": ["b"]},
        "b": {"1.0": ["a"]},
    }
    assert resolve(["a"], index) == {"a": "1.0", "b": "1.0"}


def test_cycle_with_constraints_is_tolerated():
    index = {
        "a": {"1.0": ["b>=1"], "2.0": ["b>=2"]},
        "b": {"1.0": ["a"], "2.0": ["a==2.0"]},
    }
    assert resolve(["a"], index) == {"a": "2.0", "b": "2.0"}


def test_backtracks_out_of_a_dead_end():
    # a 3.0 needs b>=2, but b 2.0 needs c>=3, which does not exist.
    index = {
        "a": {"3.0": ["b>=2"], "2.0": ["b==1.0"]},
        "b": {"1.0": [], "2.0": ["c>=3"]},
        "c": {"1.0": []},
    }
    assert resolve(["a"], index) == {"a": "2.0", "b": "1.0"}


def test_backtracks_through_a_chain_of_choices():
    # mid 2.0 would cap low below 2, so the alphabetically first package low takes 2.0
    # through mid 1.0. top 2.0 still holds because mid 1.0 is reachable.
    index = {
        "top": {"2.0": ["mid"], "1.0": []},
        "mid": {"2.0": ["low<2"], "1.0": ["low"]},
        "low": {"1.0": [], "2.0": []},
    }
    assert resolve(["top"], index) == {"top": "2.0", "mid": "1.0", "low": "2.0"}


def test_alphabetically_first_package_gets_highest_version_it_can():
    # Choosing z 2.0 would force b to 1.0. The spec prefers b 2.0, so z drops to 1.0.
    index = {
        "z": {"2.0": ["b<2"], "1.0": ["b>=0"]},
        "b": {"1.0": [], "2.0": []},
    }
    assert resolve(["z"], index) == {"b": "2.0", "z": "1.0"}


def test_present_version_beats_absent_for_alphabetically_earlier_package():
    # a can be 2.0 only if x is 1.0. Name order puts a first, so a gets 2.0 and x is 1.0.
    index = {
        "x": {"2.0": [], "1.0": ["a"]},
        "a": {"1.0": [], "2.0": []},
    }
    assert resolve(["x"], index) == {"a": "2.0", "x": "1.0"}


# resolve: errors

def test_error_names_the_leaf_package_not_the_root():
    index = {
        "a": {"1.0": ["b<1"]},
        "b": {"1": [], "2": []},
    }
    with pytest.raises(ResolutionError) as exc:
        resolve(["a"], index)
    assert "'b'" in str(exc.value)


def test_error_names_conflicting_package():
    index = {
        "app": {"1.0": ["web", "db"]},
        "web": {"1.0": ["json<3"]},
        "db": {"1.0": ["json>=3"]},
        "json": {"2.0": [], "3.0": []},
    }
    with pytest.raises(ResolutionError) as exc:
        resolve(["app"], index)
    assert "json" in str(exc.value)


def test_error_names_unsatisfiable_root():
    with pytest.raises(ResolutionError) as exc:
        resolve(["web>=5"], SPEC_INDEX)
    assert "web" in str(exc.value)


def test_error_names_missing_dependency():
    index = {"a": {"1.0": ["ghost"]}}
    with pytest.raises(ResolutionError) as exc:
        resolve(["a"], index)
    assert "ghost" in str(exc.value)


def test_error_for_missing_root():
    with pytest.raises(ResolutionError) as exc:
        resolve(["nope"], SPEC_INDEX)
    assert "nope" in str(exc.value)


def test_invalid_requirement_in_roots_raises_value_error():
    with pytest.raises(ValueError):
        resolve(["web>>2"], SPEC_INDEX)


# resolve: scale

def test_large_chain_with_a_hidden_conflict_resolves_quickly():
    # Each x_i = v forces x_{i+1} = v. The tail caps the chain at 50, and x1 >= 40.
    # Naive enumeration over 200^5 combinations would never finish.
    versions = {str(v): [] for v in range(1, 201)}
    index = {}
    for i in range(1, 5):
        index[f"x{i}"] = {str(v): [f"x{i + 1}=={v}"] for v in range(1, 201)}
    index["x5"] = versions
    start = time.monotonic()
    result = resolve(["x1>=40", "x5<=50"], index)
    elapsed = time.monotonic() - start
    assert result == {f"x{i}": "50" for i in range(1, 6)}
    assert elapsed < 10


def test_large_chain_with_no_solution_fails_quickly():
    index = {}
    for i in range(1, 5):
        index[f"x{i}"] = {str(v): [f"x{i + 1}=={v}"] for v in range(1, 201)}
    index["x5"] = {str(v): [] for v in range(1, 201)}
    start = time.monotonic()
    with pytest.raises(ResolutionError):
        resolve(["x1>=190", "x5<=50"], index)
    assert time.monotonic() - start < 10


def test_many_independent_packages_with_hundreds_of_versions():
    index = {"root": {"1.0": [f"p{i}" for i in range(8)]}}
    for i in range(8):
        index[f"p{i}"] = {str(v): [] for v in range(1, 301)}
    start = time.monotonic()
    result = resolve(["root"], index)
    assert time.monotonic() - start < 10
    assert result["root"] == "1.0"
    assert all(result[f"p{i}"] == "300" for i in range(8))
