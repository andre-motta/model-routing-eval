import copy
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from jsonpatch import PatchError, PointerError, apply_patch, resolve_pointer  # noqa: E402


# --- JSON Pointer -----------------------------------------------------------

DOC = {
    "foo": ["bar", "baz"],
    "": 0,
    "a/b": 1,
    "c%d": 2,
    "e^f": 3,
    "g|h": 4,
    "i\\j": 5,
    "k\"l": 6,
    " ": 7,
    "m~n": 8,
}


@pytest.mark.parametrize(
    "pointer, expected",
    [
        ("", DOC),
        ("/foo", ["bar", "baz"]),
        ("/foo/0", "bar"),
        ("/", 0),
        ("/a~1b", 1),
        ("/c%d", 2),
        ("/e^f", 3),
        ("/g|h", 4),
        ("/i\\j", 5),
        ("/k\"l", 6),
        ("/ ", 7),
        ("/m~0n", 8),
    ],
)
def test_resolve_rfc6901_examples(pointer, expected):
    assert resolve_pointer(DOC, pointer) == expected


def test_tilde_escape_order():
    # "~01" must unescape to "~1", not "/".
    assert resolve_pointer({"~1": "ok"}, "/~01") == "ok"


@pytest.mark.parametrize(
    "pointer",
    ["foo", "/missing", "/foo/2", "/foo/01", "/foo/-", "/foo/-1", "/foo/x",
     "/foo/0/deeper", "/a~2b", "/trailing~"],
)
def test_resolve_invalid_raises(pointer):
    with pytest.raises(PointerError):
        resolve_pointer(DOC, pointer)


def test_pointer_error_is_patch_error():
    assert issubclass(PointerError, PatchError)


# --- add --------------------------------------------------------------------

def test_add_object_member():
    assert apply_patch({"a": 1}, [{"op": "add", "path": "/b", "value": 2}]) == {"a": 1, "b": 2}


def test_add_overwrites_existing_member():
    assert apply_patch({"a": 1}, [{"op": "add", "path": "/a", "value": 9}]) == {"a": 9}


def test_add_array_insert_middle():
    doc = {"l": [1, 3]}
    assert apply_patch(doc, [{"op": "add", "path": "/l/1", "value": 2}]) == {"l": [1, 2, 3]}


def test_add_array_index_equal_len_appends():
    doc = {"l": [1, 2]}
    assert apply_patch(doc, [{"op": "add", "path": "/l/2", "value": 3}]) == {"l": [1, 2, 3]}


def test_add_array_dash_appends():
    doc = {"l": [1]}
    assert apply_patch(doc, [{"op": "add", "path": "/l/-", "value": 2}]) == {"l": [1, 2]}


def test_add_index_past_end_fails():
    with pytest.raises(PatchError):
        apply_patch({"l": [1]}, [{"op": "add", "path": "/l/5", "value": 2}])


def test_add_root_replaces_document():
    assert apply_patch({"a": 1}, [{"op": "add", "path": "", "value": [1]}]) == [1]


def test_add_missing_parent_fails():
    with pytest.raises(PointerError):
        apply_patch({}, [{"op": "add", "path": "/a/b", "value": 1}])


# --- remove -----------------------------------------------------------------

def test_remove_member_and_element():
    assert apply_patch({"a": 1, "b": 2}, [{"op": "remove", "path": "/a"}]) == {"b": 2}
    assert apply_patch({"l": [1, 2, 3]}, [{"op": "remove", "path": "/l/0"}]) == {"l": [2, 3]}


def test_remove_missing_fails():
    with pytest.raises(PatchError):
        apply_patch({"a": 1}, [{"op": "remove", "path": "/b"}])
    with pytest.raises(PatchError):
        apply_patch({"l": [1]}, [{"op": "remove", "path": "/l/3"}])


def test_remove_root_fails():
    with pytest.raises(PatchError):
        apply_patch({"a": 1}, [{"op": "remove", "path": ""}])


# --- replace ----------------------------------------------------------------

def test_replace_member_and_element():
    assert apply_patch({"a": 1}, [{"op": "replace", "path": "/a", "value": 2}]) == {"a": 2}
    assert apply_patch({"l": [1, 2]}, [{"op": "replace", "path": "/l/1", "value": 5}]) == {"l": [1, 5]}


def test_replace_root():
    assert apply_patch({"a": 1}, [{"op": "replace", "path": "", "value": "x"}]) == "x"


def test_replace_missing_fails():
    with pytest.raises(PatchError):
        apply_patch({"a": 1}, [{"op": "replace", "path": "/b", "value": 2}])


# --- move -------------------------------------------------------------------

def test_move_between_objects():
    doc = {"a": {"x": 1}, "b": {}}
    assert apply_patch(doc, [{"op": "move", "from": "/a/x", "path": "/b/y"}]) == {"a": {}, "b": {"y": 1}}


def test_move_array_element():
    doc = {"l": [1, 2, 3]}
    assert apply_patch(doc, [{"op": "move", "from": "/l/0", "path": "/l/2"}]) == {"l": [2, 3, 1]}


def test_move_to_same_location_is_noop():
    doc = {"a": 1}
    assert apply_patch(doc, [{"op": "move", "from": "/a", "path": "/a"}]) == {"a": 1}


def test_move_into_own_child_fails():
    with pytest.raises(PatchError):
        apply_patch({"a": {"b": 1}}, [{"op": "move", "from": "/a", "path": "/a/c"}])


def test_move_missing_from_fails():
    with pytest.raises(PatchError):
        apply_patch({"a": 1}, [{"op": "move", "from": "/z", "path": "/b"}])


# --- copy -------------------------------------------------------------------

def test_copy_is_deep():
    doc = {"a": {"x": [1]}}
    result = apply_patch(doc, [{"op": "copy", "from": "/a", "path": "/b"}])
    assert result == {"a": {"x": [1]}, "b": {"x": [1]}}
    result["b"]["x"].append(2)
    assert result["a"]["x"] == [1]


def test_copy_missing_from_fails():
    with pytest.raises(PatchError):
        apply_patch({"a": 1}, [{"op": "copy", "from": "/z", "path": "/b"}])


# --- test -------------------------------------------------------------------

def test_test_success_and_failure():
    doc = {"a": [1, {"b": "c"}]}
    assert apply_patch(doc, [{"op": "test", "path": "/a", "value": [1, {"b": "c"}]}]) == doc
    with pytest.raises(PatchError):
        apply_patch(doc, [{"op": "test", "path": "/a/0", "value": 2}])


def test_test_numbers_compare_by_value():
    assert apply_patch({"n": 1}, [{"op": "test", "path": "/n", "value": 1.0}]) == {"n": 1}


def test_test_bool_is_not_number():
    with pytest.raises(PatchError):
        apply_patch({"n": 1}, [{"op": "test", "path": "/n", "value": True}])
    with pytest.raises(PatchError):
        apply_patch({"n": True}, [{"op": "test", "path": "/n", "value": 1}])
    with pytest.raises(PatchError):
        apply_patch({"n": False}, [{"op": "test", "path": "/n", "value": 0}])


def test_test_null_and_string_mismatch():
    with pytest.raises(PatchError):
        apply_patch({"n": None}, [{"op": "test", "path": "/n", "value": ""}])


def test_test_dict_key_sets_must_match():
    with pytest.raises(PatchError):
        apply_patch({"d": {"a": 1}}, [{"op": "test", "path": "/d", "value": {"a": 1, "b": 2}}])


# --- atomicity and mutation -------------------------------------------------

def test_failure_leaves_input_unchanged():
    doc = {"a": 1, "l": [1, 2]}
    original = copy.deepcopy(doc)
    patch = [
        {"op": "add", "path": "/b", "value": 2},
        {"op": "remove", "path": "/l/0"},
        {"op": "remove", "path": "/missing"},
    ]
    with pytest.raises(PatchError):
        apply_patch(doc, patch)
    assert doc == original


def test_default_does_not_mutate_input_on_success():
    doc = {"a": [1]}
    original = copy.deepcopy(doc)
    result = apply_patch(doc, [{"op": "add", "path": "/a/-", "value": 2}])
    assert result == {"a": [1, 2]}
    assert doc == original


def test_result_does_not_alias_input_value():
    value = {"k": [1]}
    result = apply_patch({}, [{"op": "add", "path": "/v", "value": value}])
    result["v"]["k"].append(2)
    assert value == {"k": [1]}


def test_in_place_mutates_on_success():
    doc = {"a": 1}
    result = apply_patch(doc, [{"op": "replace", "path": "/a", "value": 2}], in_place=True)
    assert doc == {"a": 2}
    assert result is doc


def test_in_place_list_root_mutates_on_success():
    doc = [1, 2]
    apply_patch(doc, [{"op": "remove", "path": "/0"}], in_place=True)
    assert doc == [2]


def test_in_place_untouched_on_failure():
    doc = {"a": 1}
    with pytest.raises(PatchError):
        apply_patch(doc, [{"op": "replace", "path": "/a", "value": 2},
                          {"op": "test", "path": "/a", "value": 1}], in_place=True)
    assert doc == {"a": 1}


def test_operations_apply_in_order():
    doc = {}
    patch = [
        {"op": "add", "path": "/a", "value": 1},
        {"op": "copy", "from": "/a", "path": "/b"},
        {"op": "move", "from": "/a", "path": "/c"},
    ]
    assert apply_patch(doc, patch) == {"b": 1, "c": 1}


# --- validation -------------------------------------------------------------

@pytest.mark.parametrize(
    "op",
    [
        {"op": "frobnicate", "path": "/a"},
        {"path": "/a", "value": 1},
        {"op": "add", "value": 1},
        {"op": "add", "path": "/a"},
        {"op": "test", "path": "/a"},
        {"op": "move", "path": "/a"},
        {"op": "copy", "from": 3, "path": "/a"},
        {"op": "add", "path": 3, "value": 1},
        {"op": 1, "path": "/a", "value": 1},
        "add /a",
        None,
    ],
)
def test_invalid_operations_raise(op):
    with pytest.raises(PatchError):
        apply_patch({"a": 1}, [op])


def test_patch_must_be_list():
    with pytest.raises(PatchError):
        apply_patch({}, {"op": "add", "path": "/a", "value": 1})


def test_empty_patch_returns_copy():
    doc = {"a": [1]}
    result = apply_patch(doc, [])
    assert result == doc
    assert result is not doc
