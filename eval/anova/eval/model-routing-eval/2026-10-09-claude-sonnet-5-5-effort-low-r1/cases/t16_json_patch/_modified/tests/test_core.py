import pytest

from jsonpatch.core import PatchError, PointerError, apply_patch, resolve_pointer


def test_pointer():
    d = {"a/b": [1, {"~": 2}], "": 0}
    assert resolve_pointer(d, "") is d
    assert resolve_pointer(d, "/a~1b/1/~0") == 2
    assert resolve_pointer(d, "/") == 0
    for p in ["a", "/a~1b/01", "/a~1b/-", "/a~1b/2", "/x", "/a~1b/0/1", "/a~1b/+1"]:
        with pytest.raises(PointerError):
            resolve_pointer(d, p)


def test_add_variants():
    assert apply_patch([1], [{"op": "add", "path": "/-", "value": 2}]) == [1, 2]
    assert apply_patch([1], [{"op": "add", "path": "/1", "value": 2}]) == [1, 2]
    assert apply_patch([1], [{"op": "add", "path": "/0", "value": 0}]) == [0, 1]
    assert apply_patch({}, [{"op": "add", "path": "", "value": 5}]) == 5
    with pytest.raises(PatchError):
        apply_patch([1], [{"op": "add", "path": "/2", "value": 0}])


def test_remove_replace():
    assert apply_patch({"a": 1}, [{"op": "remove", "path": "/a"}]) == {}
    with pytest.raises(PatchError):
        apply_patch({}, [{"op": "remove", "path": "/a"}])
    with pytest.raises(PatchError):
        apply_patch([1], [{"op": "replace", "path": "/1", "value": 1}])
    assert apply_patch([1, 2], [{"op": "replace", "path": "/1", "value": 9}]) == [1, 9]
    assert apply_patch(1, [{"op": "replace", "path": "", "value": None}]) is None


def test_move_copy():
    assert apply_patch({"a": [1, 2]}, [{"op": "move", "from": "/a/0", "path": "/a/1"}]) == {"a": [2, 1]}
    with pytest.raises(PatchError):
        apply_patch({"a": {}}, [{"op": "move", "from": "/a", "path": "/a/b"}])
    d = {"a": {"x": 1}}
    out = apply_patch(d, [{"op": "copy", "from": "/a", "path": "/b"}, {"op": "add", "path": "/b/y", "value": 2}])
    assert out == {"a": {"x": 1}, "b": {"x": 1, "y": 2}}
    assert apply_patch({"a": 1}, [{"op": "move", "from": "/a", "path": "/a"}]) == {"a": 1}


def test_test_op():
    ok = lambda v, t: apply_patch({"a": v}, [{"op": "test", "path": "/a", "value": t}])
    ok(1, 1.0)
    ok([1, {"b": 2}], [1.0, {"b": 2}])
    for v, t in [(True, 1), (1, True), (0, False), ([True], [1]), ({"a": 1}, {"a": 1, "b": 2})]:
        with pytest.raises(PatchError):
            ok(v, t)


def test_atomic_and_in_place():
    d = {"a": [1]}
    bad = [{"op": "add", "path": "/a/-", "value": 2}, {"op": "remove", "path": "/zz"}]
    for ip in (False, True):
        with pytest.raises(PatchError):
            apply_patch(d, bad, in_place=ip)
        assert d == {"a": [1]}
    out = apply_patch(d, [{"op": "add", "path": "/a/-", "value": 2}])
    assert d == {"a": [1]} and out == {"a": [1, 2]}
    out = apply_patch(d, [{"op": "add", "path": "/a/-", "value": 2}], in_place=True)
    assert out is d and d == {"a": [1, 2]}


def test_value_not_aliased():
    v = [1]
    out = apply_patch({}, [{"op": "add", "path": "/a", "value": v}])
    v.append(2)
    assert out == {"a": [1]}


@pytest.mark.parametrize("op", [
    {"op": "bogus", "path": ""}, {"path": "/a"}, {"op": "add", "path": "/a"},
    {"op": "move", "path": "/a"}, {"op": "remove", "path": 3}, "x",
    {"op": "test", "path": "/a"},
])
def test_malformed(op):
    with pytest.raises(PatchError):
        apply_patch({"a": 1}, [op])
    with pytest.raises(PatchError):
        apply_patch({}, {"op": "add"})
