import copy

import pytest

from jsonpatch import apply_patch, resolve_pointer, PatchError, PointerError

DOC = {"foo": ["bar", "baz"], "": 0, "a/b": 1, "c%d": 2, "e^f": 3, "g|h": 4, "i\\j": 5, "k\"l": 6, " ": 7, "m~n": 8}


def test_pointer_rfc_examples():
    assert resolve_pointer(DOC, "") == DOC
    assert resolve_pointer(DOC, "/foo") == ["bar", "baz"]
    assert resolve_pointer(DOC, "/foo/0") == "bar"
    assert resolve_pointer(DOC, "/") == 0
    assert resolve_pointer(DOC, "/a~1b") == 1
    assert resolve_pointer(DOC, "/m~0n") == 8
    assert resolve_pointer(DOC, "/ ") == 7
    assert resolve_pointer({"~1": "x"}, "/~01") == "x"


def test_pointer_errors():
    for p in ("foo", "/foo/01", "/foo/2", "/foo/-", "/nope", "/foo/x"):
        with pytest.raises(PointerError):
            resolve_pointer(DOC, p)


def test_add_variants():
    assert apply_patch({"foo": "bar"}, [{"op": "add", "path": "/baz", "value": "qux"}]) == {"foo": "bar", "baz": "qux"}
    assert apply_patch({"foo": ["bar", "baz"]}, [{"op": "add", "path": "/foo/1", "value": "qux"}]) == {"foo": ["bar", "qux", "baz"]}
    assert apply_patch({"foo": ["bar"]}, [{"op": "add", "path": "/foo/-", "value": ["abc", "def"]}]) == {"foo": ["bar", ["abc", "def"]]}
    assert apply_patch({"foo": ["bar"]}, [{"op": "add", "path": "/foo/1", "value": "x"}]) == {"foo": ["bar", "x"]}
    assert apply_patch({"foo": "bar"}, [{"op": "add", "path": "", "value": [1]}]) == [1]
    assert apply_patch({"foo": "bar"}, [{"op": "add", "path": "/foo", "value": "new"}]) == {"foo": "new"}
    with pytest.raises(PatchError):
        apply_patch({"foo": ["bar"]}, [{"op": "add", "path": "/foo/2", "value": "x"}])
    with pytest.raises(PatchError):
        apply_patch({"foo": "bar"}, [{"op": "add", "path": "/baz/bat", "value": "qux"}])


def test_remove_replace():
    assert apply_patch({"baz": "qux", "foo": "bar"}, [{"op": "remove", "path": "/baz"}]) == {"foo": "bar"}
    assert apply_patch({"foo": ["bar", "qux", "baz"]}, [{"op": "remove", "path": "/foo/1"}]) == {"foo": ["bar", "baz"]}
    assert apply_patch({"baz": "qux", "foo": "bar"}, [{"op": "replace", "path": "/baz", "value": "boo"}]) == {"baz": "boo", "foo": "bar"}
    with pytest.raises(PatchError):
        apply_patch({"foo": "bar"}, [{"op": "replace", "path": "/baz", "value": 1}])
    with pytest.raises(PatchError):
        apply_patch({"foo": "bar"}, [{"op": "remove", "path": "/baz"}])


def test_move_copy():
    d = {"foo": {"bar": "baz", "waldo": "fred"}, "qux": {"corge": "grault"}}
    assert apply_patch(d, [{"op": "move", "from": "/foo/waldo", "path": "/qux/thud"}]) == {"foo": {"bar": "baz"}, "qux": {"corge": "grault", "thud": "fred"}}
    assert apply_patch({"foo": ["all", "grass", "cows", "eat"]}, [{"op": "move", "from": "/foo/1", "path": "/foo/3"}]) == {"foo": ["all", "cows", "eat", "grass"]}
    assert apply_patch({"baz": [{"qux": "hello"}], "bar": 1}, [{"op": "copy", "from": "/baz/0", "path": "/boo"}]) == {"baz": [{"qux": "hello"}], "bar": 1, "boo": {"qux": "hello"}}
    out = apply_patch({"a": {"b": [1]}}, [{"op": "copy", "from": "/a", "path": "/c"}])
    out["c"]["b"].append(2)
    assert out["a"]["b"] == [1], "copy must be deep"
    with pytest.raises(PatchError):
        apply_patch({"a": {"b": 1}}, [{"op": "move", "from": "/a", "path": "/a/b/c"}])
    assert apply_patch({"a": {"b": 1}}, [{"op": "move", "from": "/a", "path": "/a"}]) == {"a": {"b": 1}}


def test_test_op_semantics():
    d = {"baz": "qux", "foo": ["a", 2, "c"], "n": 1, "t": True}
    apply_patch(d, [{"op": "test", "path": "/baz", "value": "qux"}, {"op": "test", "path": "/foo/1", "value": 2}])
    apply_patch(d, [{"op": "test", "path": "/n", "value": 1.0}])
    with pytest.raises(PatchError):
        apply_patch(d, [{"op": "test", "path": "/t", "value": 1}])
    with pytest.raises(PatchError):
        apply_patch(d, [{"op": "test", "path": "/baz", "value": "bar"}])
    apply_patch(d, [{"op": "test", "path": "/foo", "value": ["a", 2.0, "c"]}])


def test_atomic_and_in_place():
    d = {"a": 1}
    snap = copy.deepcopy(d)
    with pytest.raises(PatchError):
        apply_patch(d, [{"op": "add", "path": "/b", "value": 2}, {"op": "remove", "path": "/zzz"}])
    assert d == snap
    out = apply_patch(d, [{"op": "add", "path": "/b", "value": 2}])
    assert out == {"a": 1, "b": 2} and d == snap
    out2 = apply_patch(d, [{"op": "add", "path": "/b", "value": 2}], in_place=True)
    assert out2 is d and d == {"a": 1, "b": 2}
    with pytest.raises(PatchError):
        apply_patch(d, [{"op": "replace", "path": "/b", "value": 3}, {"op": "bogus", "path": "/b"}], in_place=True)
    assert d == {"a": 1, "b": 2}


def test_validation():
    for bad in ([{"path": "/a"}], [{"op": "add", "value": 1}], [{"op": "add", "path": "/a"}], [{"op": "move", "path": "/a"}], "notalist", [{"op": "test", "path": 5, "value": 1}]):
        with pytest.raises(PatchError):
            apply_patch({"a": 1}, bad)
