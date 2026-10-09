import copy

import pytest

from jsonpatch import PatchError, PointerError, apply_patch, resolve_pointer


DOC = {"a": {"b": [10, 20, 30]}, "x/y": 1, "m~n": 2, "": 3}


@pytest.mark.parametrize(
    "pointer,expected",
    [
        ("", DOC),
        ("/a/b/0", 10),
        ("/a/b/2", 30),
        ("/x~1y", 1),
        ("/m~0n", 2),
        ("/", 3),
    ],
)
def test_resolve_ok(pointer, expected):
    assert resolve_pointer(DOC, pointer) == expected


def test_unescape_order():
    assert resolve_pointer({"~1": 5}, "/~01") == 5


@pytest.mark.parametrize(
    "pointer",
    ["a", "/a/b/01", "/a/b/-", "/a/b/3", "/a/b/-1", "/a/b/x", "/nope", "/a/b/0/z", "/a/b/٣", 5, None],
)
def test_resolve_errors(pointer):
    with pytest.raises(PointerError):
        resolve_pointer(DOC, pointer)


def test_pointer_error_is_patch_error():
    assert issubclass(PointerError, PatchError)


def test_add_object_and_array():
    doc = {"a": [1, 2]}
    out = apply_patch(doc, [
        {"op": "add", "path": "/b", "value": None},
        {"op": "add", "path": "/a/1", "value": "x"},
        {"op": "add", "path": "/a/-", "value": "end"},
        {"op": "add", "path": "/a/4", "value": "e2"},
    ])
    assert out == {"a": [1, "x", 2, "end", "e2"], "b": None}
    assert doc == {"a": [1, 2]}


def test_add_errors():
    with pytest.raises(PatchError):
        apply_patch({"a": [1]}, [{"op": "add", "path": "/a/3", "value": 1}])
    with pytest.raises(PatchError):
        apply_patch({}, [{"op": "add", "path": "/a/b", "value": 1}])
    with pytest.raises(PatchError):
        apply_patch({"a": 1}, [{"op": "add", "path": "/a/b", "value": 1}])
    with pytest.raises(PatchError):
        apply_patch({}, [{"op": "add", "path": "/a"}])


def test_add_root():
    assert apply_patch({"a": 1}, [{"op": "add", "path": "", "value": [1]}]) == [1]
    assert apply_patch(5, [{"op": "add", "path": "", "value": {"k": 1}}]) == {"k": 1}


def test_remove_replace():
    doc = {"a": [1, 2, 3], "b": 1}
    out = apply_patch(doc, [
        {"op": "remove", "path": "/a/0"},
        {"op": "replace", "path": "/b", "value": "z"},
        {"op": "replace", "path": "/a/1", "value": 9},
    ])
    assert out == {"a": [2, 9], "b": "z"}


@pytest.mark.parametrize(
    "op",
    [
        {"op": "remove", "path": "/nope"},
        {"op": "remove", "path": "/a/3"},
        {"op": "remove", "path": "/a/-"},
        {"op": "replace", "path": "/nope", "value": 1},
        {"op": "replace", "path": "/a/3", "value": 1},
        {"op": "replace", "path": "/a/-", "value": 1},
    ],
)
def test_missing_targets(op):
    with pytest.raises(PatchError):
        apply_patch({"a": [1, 2, 3]}, [op])


def test_replace_root():
    assert apply_patch({"a": 1}, [{"op": "replace", "path": "", "value": 2}]) == 2


def test_move():
    doc = {"a": {"b": 1}, "list": [1, 2, 3]}
    out = apply_patch(doc, [
        {"op": "move", "from": "/a/b", "path": "/c"},
        {"op": "move", "from": "/list/0", "path": "/list/2"},
    ])
    assert out == {"a": {}, "c": 1, "list": [2, 3, 1]}


def test_move_into_child_rejected():
    with pytest.raises(PatchError):
        apply_patch({"a": {"b": 1}}, [{"op": "move", "from": "/a", "path": "/a/b"}])
    with pytest.raises(PatchError):
        apply_patch({"a": 1}, [{"op": "move", "from": "", "path": "/a"}])


def test_move_prefix_is_token_based():
    out = apply_patch({"a": 1}, [{"op": "move", "from": "/a", "path": "/ab"}])
    assert out == {"ab": 1}


def test_move_same_path_noop_but_must_exist():
    assert apply_patch({"a": 1}, [{"op": "move", "from": "/a", "path": "/a"}]) == {"a": 1}
    with pytest.raises(PatchError):
        apply_patch({"a": 1}, [{"op": "move", "from": "/b", "path": "/b"}])


def test_move_missing_from():
    with pytest.raises(PatchError):
        apply_patch({}, [{"op": "move", "from": "/a", "path": "/b"}])


def test_copy_is_deep():
    doc = {"a": {"b": [1]}}
    out = apply_patch(doc, [{"op": "copy", "from": "/a", "path": "/c"}])
    out["c"]["b"].append(2)
    assert out["a"]["b"] == [1]
    assert doc == {"a": {"b": [1]}}
    with pytest.raises(PatchError):
        apply_patch(doc, [{"op": "copy", "from": "/zz", "path": "/c"}])


def test_value_not_aliased():
    value = {"k": [1]}
    out = apply_patch({}, [{"op": "add", "path": "/v", "value": value}])
    out["v"]["k"].append(2)
    assert value == {"k": [1]}


@pytest.mark.parametrize(
    "target,value,ok",
    [
        (1, 1.0, True),
        (1.0, 1, True),
        (True, 1, False),
        (1, True, False),
        (False, 0, False),
        (True, True, True),
        ([1, 2], [1.0, 2], True),
        ([True], [1], False),
        ({"a": [1]}, {"a": [True]}, False),
        ({"a": 1}, {"a": 1.0}, True),
        ({"a": 1}, {"a": 1, "b": 2}, False),
        (None, None, True),
        (None, 0, False),
        ("1", 1, False),
        ([], {}, False),
        ({}, [], False),
    ],
)
def test_test_op(target, value, ok):
    patch = [{"op": "test", "path": "/t", "value": value}]
    doc = {"t": target}
    if ok:
        assert apply_patch(doc, patch) == doc
    else:
        with pytest.raises(PatchError):
            apply_patch(doc, patch)


def test_test_missing_path_fails():
    with pytest.raises(PatchError):
        apply_patch({}, [{"op": "test", "path": "/a", "value": None}])


def test_atomic_not_in_place():
    doc = {"a": [1, 2], "b": {"c": 1}}
    snapshot = copy.deepcopy(doc)
    with pytest.raises(PatchError):
        apply_patch(doc, [
            {"op": "remove", "path": "/a/0"},
            {"op": "add", "path": "/b/d", "value": 1},
            {"op": "test", "path": "/b/c", "value": 99},
        ])
    assert doc == snapshot


def test_atomic_in_place_failure_untouched():
    doc = {"a": [1, 2]}
    snapshot = copy.deepcopy(doc)
    with pytest.raises(PatchError):
        apply_patch(doc, [
            {"op": "remove", "path": "/a/0"},
            {"op": "remove", "path": "/nope"},
        ], in_place=True)
    assert doc == snapshot


def test_in_place_success_mutates():
    doc = {"a": [1, 2]}
    inner = doc["a"]
    out = apply_patch(doc, [{"op": "add", "path": "/b", "value": 1}], in_place=True)
    assert out is doc
    assert doc == {"a": [1, 2], "b": 1}
    assert inner == [1, 2]


def test_in_place_list_root_and_root_replace():
    lst = [1]
    out = apply_patch(lst, [{"op": "add", "path": "/-", "value": 2}], in_place=True)
    assert out is lst and lst == [1, 2]
    out = apply_patch({"a": 1}, [{"op": "replace", "path": "", "value": 3}], in_place=True)
    assert out == 3


def test_not_in_place_never_mutates_input():
    doc = {"a": [1]}
    out = apply_patch(doc, [{"op": "add", "path": "/a/-", "value": 2}])
    assert doc == {"a": [1]} and out == {"a": [1, 2]}


@pytest.mark.parametrize(
    "patch",
    [
        "nope",
        {"op": "add"},
        [5],
        [{}],
        [{"op": "bogus", "path": ""}],
        [{"op": 1, "path": ""}],
        [{"op": "add", "value": 1}],
        [{"op": "add", "path": 1, "value": 1}],
        [{"op": "move", "path": "/a"}],
        [{"op": "copy", "path": "/a"}],
        [{"op": "move", "from": 1, "path": "/a"}],
        [{"op": "test", "path": "/a"}],
        [{"op": "replace", "path": "/a"}],
        [{"op": "remove"}],
        [{"op": "add", "path": "bad", "value": 1}],
    ],
)
def test_malformed(patch):
    with pytest.raises(PatchError):
        apply_patch({"a": 1}, patch)


def test_empty_patch():
    doc = {"a": 1}
    assert apply_patch(doc, []) == doc
    assert apply_patch(doc, []) is not doc


def test_ops_apply_in_order():
    out = apply_patch({}, [
        {"op": "add", "path": "/a", "value": 1},
        {"op": "copy", "from": "/a", "path": "/b"},
        {"op": "test", "path": "/b", "value": 1},
        {"op": "move", "from": "/b", "path": "/c"},
        {"op": "remove", "path": "/a"},
    ])
    assert out == {"c": 1}
