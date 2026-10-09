import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from jsonpatch.core import PatchError, PointerError, apply_patch, resolve_pointer


def test_pointer():
    d = {"a/b": [1, {"m~n": 2}], "": 5}
    assert resolve_pointer(d, "") is d
    assert resolve_pointer(d, "/a~1b/1/m~0n") == 2
    assert resolve_pointer(d, "/") == 5
    for bad in ["a", "/a~1b/01", "/a~1b/-", "/a~1b/2", "/nope", "/a~1b/x", "/a~1b/0/x"]:
        with pytest.raises(PointerError):
            resolve_pointer(d, bad)


def test_add_variants():
    assert apply_patch({}, [{"op": "add", "path": "", "value": 3}]) == 3
    assert apply_patch([1, 2], [{"op": "add", "path": "/-", "value": 3}]) == [1, 2, 3]
    assert apply_patch([1, 2], [{"op": "add", "path": "/2", "value": 3}]) == [1, 2, 3]
    assert apply_patch([1, 2], [{"op": "add", "path": "/0", "value": 0}]) == [0, 1, 2]
    with pytest.raises(PatchError):
        apply_patch([1], [{"op": "add", "path": "/3", "value": 0}])
    with pytest.raises(PatchError):
        apply_patch({}, [{"op": "add", "path": "/a/b", "value": 0}])


def test_remove_replace():
    assert apply_patch({"a": 1}, [{"op": "remove", "path": "/a"}]) == {}
    with pytest.raises(PatchError):
        apply_patch({"a": 1}, [{"op": "remove", "path": "/b"}])
    with pytest.raises(PatchError):
        apply_patch([1], [{"op": "remove", "path": "/1"}])
    with pytest.raises(PatchError):
        apply_patch([1], [{"op": "remove", "path": "/-"}])
    assert apply_patch([1, 2], [{"op": "replace", "path": "/1", "value": 9}]) == [1, 9]
    assert apply_patch({"a": 1}, [{"op": "replace", "path": "", "value": None}]) is None
    with pytest.raises(PatchError):
        apply_patch({}, [{"op": "replace", "path": "/a", "value": 1}])


def test_move_copy():
    assert apply_patch({"a": 1}, [{"op": "move", "path": "/b", "from": "/a"}]) == {"b": 1}
    assert apply_patch([1, 2, 3], [{"op": "move", "path": "/2", "from": "/0"}]) == [2, 3, 1]
    with pytest.raises(PatchError):
        apply_patch({"a": {"b": 1}}, [{"op": "move", "path": "/a/b/c", "from": "/a"}])
    with pytest.raises(PatchError):
        apply_patch({}, [{"op": "move", "path": "/b", "from": "/a"}])
    d = {"a": {"x": [1]}}
    r = apply_patch(d, [{"op": "copy", "path": "/b", "from": "/a"}])
    r["b"]["x"].append(2)
    assert r["a"]["x"] == [1]


def test_test_op():
    ok = lambda v, t: apply_patch({"a": v}, [{"op": "test", "path": "/a", "value": t}])
    ok(1, 1.0)
    ok({"x": [1, 2]}, {"x": [1.0, 2]})
    for v, t in [(True, 1), (1, True), (0, False), ({"x": True}, {"x": 1}), ([1], [1, 2]), (None, 0)]:
        with pytest.raises(PatchError):
            ok(v, t)
    ok(True, True)


def test_atomic_and_in_place():
    d = {"a": [1, 2]}
    orig = copy.deepcopy(d)
    bad = [{"op": "add", "path": "/a/-", "value": 3}, {"op": "remove", "path": "/zz"}]
    for ip in (False, True):
        with pytest.raises(PatchError):
            apply_patch(d, bad, in_place=ip)
        assert d == orig
    good = [{"op": "add", "path": "/a/-", "value": 3}]
    r = apply_patch(d, good)
    assert d == orig and r["a"] == [1, 2, 3]
    r = apply_patch(d, good, in_place=True)
    assert r is d and d["a"] == [1, 2, 3]


def test_input_value_not_aliased():
    v = {"k": []}
    r = apply_patch({}, [{"op": "add", "path": "/a", "value": v}])
    r["a"]["k"].append(1)
    assert v == {"k": []}


@pytest.mark.parametrize("patch", [
    {"op": "add"}, [1], [{"op": "bogus", "path": ""}], [{"op": "add", "path": "/a"}],
    [{"op": "move", "path": "/a"}], [{"op": "add", "path": 1, "value": 1}],
    [{"op": "copy", "path": "/a", "from": 3}], [{"path": "/a"}],
])
def test_malformed(patch):
    with pytest.raises(PatchError):
        apply_patch({"a": 1}, patch)
