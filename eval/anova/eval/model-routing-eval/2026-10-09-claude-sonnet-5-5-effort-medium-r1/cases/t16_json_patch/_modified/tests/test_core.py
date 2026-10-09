import copy

import pytest

from jsonpatch import PatchError, PointerError, apply_patch, resolve_pointer


# --- pointers ---

def test_pointer_basic():
    doc = {"a": [10, {"b": 2}], "": 1, "a/b": 3, "m~n": 4}
    assert resolve_pointer(doc, "") is doc
    assert resolve_pointer(doc, "/a/0") == 10
    assert resolve_pointer(doc, "/a/1/b") == 2
    assert resolve_pointer(doc, "/") == 1
    assert resolve_pointer(doc, "/a~1b") == 3
    assert resolve_pointer(doc, "/m~0n") == 4


def test_pointer_unescape_order():
    assert resolve_pointer({"~1": 5}, "/~01") == 5


@pytest.mark.parametrize("ptr", ["a", "/a/01", "/a/-", "/a/5", "/a/x", "/a/-1", "/zz", "/a/0/x"])
def test_pointer_errors(ptr):
    with pytest.raises(PointerError):
        resolve_pointer({"a": [1]}, ptr)


def test_pointer_non_string():
    with pytest.raises(PointerError):
        resolve_pointer({}, None)


# --- operations ---

def test_add_object_array_root():
    assert apply_patch({}, [{"op": "add", "path": "/a", "value": 1}]) == {"a": 1}
    assert apply_patch([1, 3], [{"op": "add", "path": "/1", "value": 2}]) == [1, 2, 3]
    assert apply_patch([1], [{"op": "add", "path": "/1", "value": 2}]) == [1, 2]
    assert apply_patch([1], [{"op": "add", "path": "/-", "value": 2}]) == [1, 2]
    assert apply_patch({"a": 1}, [{"op": "add", "path": "", "value": [9]}]) == [9]


def test_add_errors():
    for doc, path in [([1], "/3"), ({}, "/a/b"), ([1], "/01"), ([1], "/x"), (5, "/a")]:
        with pytest.raises(PatchError):
            apply_patch(doc, [{"op": "add", "path": path, "value": 0}])


def test_remove_replace():
    assert apply_patch({"a": 1, "b": 2}, [{"op": "remove", "path": "/a"}]) == {"b": 2}
    assert apply_patch([1, 2, 3], [{"op": "remove", "path": "/1"}]) == [1, 3]
    assert apply_patch([1, 2], [{"op": "replace", "path": "/0", "value": 9}]) == [9, 2]
    assert apply_patch({"a": 1}, [{"op": "replace", "path": "", "value": 3}]) == 3
    for op in ("remove", "replace"):
        for path in ("/nope", "/-"):
            with pytest.raises(PatchError):
                apply_patch({"a": 1}, [{"op": op, "path": path, "value": 1}])
    with pytest.raises(PatchError):
        apply_patch([1], [{"op": "remove", "path": "/-"}])
    with pytest.raises(PatchError):
        apply_patch([1], [{"op": "replace", "path": "/1", "value": 0}])


def test_move():
    assert apply_patch({"a": 1}, [{"op": "move", "from": "/a", "path": "/b"}]) == {"b": 1}
    assert apply_patch([1, 2, 3], [{"op": "move", "from": "/0", "path": "/2"}]) == [2, 3, 1]
    assert apply_patch({"a": 1}, [{"op": "move", "from": "/a", "path": "/a"}]) == {"a": 1}
    # string prefix that is not a token prefix is fine
    assert apply_patch({"a": 1}, [{"op": "move", "from": "/a", "path": "/ab"}]) == {"ab": 1}


def test_move_into_child_and_missing():
    with pytest.raises(PatchError):
        apply_patch({"a": {"b": 1}}, [{"op": "move", "from": "/a", "path": "/a/c"}])
    with pytest.raises(PatchError):
        apply_patch({"a": 1}, [{"op": "move", "from": "/x", "path": "/b"}])


def test_copy_is_deep():
    out = apply_patch({"a": {"x": [1]}}, [{"op": "copy", "from": "/a", "path": "/b"}])
    out["b"]["x"].append(2)
    assert out["a"]["x"] == [1]
    with pytest.raises(PatchError):
        apply_patch({}, [{"op": "copy", "from": "/x", "path": "/y"}])


def test_add_value_not_aliased():
    value = {"k": [1]}
    out = apply_patch({}, [{"op": "add", "path": "/a", "value": value}])
    out["a"]["k"].append(2)
    assert value == {"k": [1]}


def test_test_op():
    ok = [
        ({"a": 1}, "/a", 1.0),
        ({"a": [1, {"b": 2}]}, "/a", [1.0, {"b": 2}]),
        ({"a": True}, "/a", True),
        ({"a": None}, "/a", None),
        ({"a": "x"}, "/a", "x"),
    ]
    for doc, path, val in ok:
        assert apply_patch(doc, [{"op": "test", "path": path, "value": val}]) == doc
    bad = [
        ({"a": True}, "/a", 1),
        ({"a": 1}, "/a", True),
        ({"a": False}, "/a", 0),
        ({"a": [True]}, "/a", [1]),
        ({"a": {"x": 1}}, "/a", {"x": 1, "y": 2}),
        ({"a": 1}, "/a", "1"),
        ({"a": 1}, "/zz", 1),
    ]
    for doc, path, val in bad:
        with pytest.raises(PatchError):
            apply_patch(doc, [{"op": "test", "path": path, "value": val}])


# --- validation ---

@pytest.mark.parametrize("op", [
    {"op": "bogus", "path": "/a"},
    {"path": "/a"},
    {"op": "add", "path": "/a"},
    {"op": "add", "value": 1},
    {"op": "replace", "path": "/a"},
    {"op": "test", "path": "/a"},
    {"op": "move", "path": "/a"},
    {"op": "copy", "path": "/a"},
    {"op": "add", "path": 5, "value": 1},
    {"op": 5, "path": "/a"},
    "notadict",
])
def test_invalid_ops(op):
    with pytest.raises(PatchError):
        apply_patch({"a": 1}, [op])


def test_patch_not_list():
    with pytest.raises(PatchError):
        apply_patch({}, {"op": "add"})


def test_test_value_none_allowed():
    assert apply_patch({"a": None}, [{"op": "test", "path": "/a", "value": None}]) == {"a": None}


# --- atomicity / mutation ---

PATCH = [
    {"op": "add", "path": "/b", "value": 2},
    {"op": "remove", "path": "/a/0"},
    {"op": "remove", "path": "/missing"},
]


@pytest.mark.parametrize("in_place", [False, True])
def test_atomic_failure(in_place):
    doc = {"a": [1, 2]}
    orig = copy.deepcopy(doc)
    with pytest.raises(PatchError):
        apply_patch(doc, PATCH, in_place=in_place)
    assert doc == orig


def test_not_in_place_leaves_input():
    doc = {"a": [1, 2]}
    out = apply_patch(doc, PATCH[:2])
    assert doc == {"a": [1, 2]}
    assert out == {"a": [2], "b": 2}


def test_in_place_mutates():
    doc = {"a": [1, 2]}
    out = apply_patch(doc, PATCH[:2], in_place=True)
    assert doc == {"a": [2], "b": 2}
    assert out is doc
    lst = [1]
    assert apply_patch(lst, [{"op": "add", "path": "/-", "value": 2}], in_place=True) is lst
    assert lst == [1, 2]


def test_in_place_root_replace():
    doc = {"a": 1}
    out = apply_patch(doc, [{"op": "replace", "path": "", "value": [1]}], in_place=True)
    assert out == [1]


def test_sequential_order():
    out = apply_patch({}, [
        {"op": "add", "path": "/a", "value": []},
        {"op": "add", "path": "/a/-", "value": 1},
        {"op": "add", "path": "/a/-", "value": 2},
        {"op": "test", "path": "/a", "value": [1, 2]},
    ])
    assert out == {"a": [1, 2]}


def test_empty_patch():
    doc = {"a": 1}
    out = apply_patch(doc, [])
    assert out == doc and out is not doc
