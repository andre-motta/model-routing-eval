import copy

import pytest

from jsonpatch import PatchError, PointerError, apply_patch, resolve_pointer


RFC_DOC = {
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
        ("", RFC_DOC),
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
def test_resolve_pointer_rfc6901_examples(pointer, expected):
    assert resolve_pointer(RFC_DOC, pointer) == expected


def test_tilde_escapes_apply_in_order():
    doc = {"~1": "tilde-one", "/": "slash"}
    # "~01" must unescape to "~1", not "/".
    assert resolve_pointer({"~1": "x"}, "/~01") == "x"
    assert resolve_pointer(doc, "/~01") == "tilde-one"


@pytest.mark.parametrize(
    "pointer",
    [
        "foo",
        "/missing",
        "/foo/2",
        "/foo/01",
        "/foo/-",
        "/foo/-1",
        "/foo/x",
        "/foo/0/deeper",
        None,
        5,
    ],
)
def test_resolve_pointer_invalid_raises(pointer):
    with pytest.raises(PointerError):
        resolve_pointer(RFC_DOC, pointer)


def test_pointer_error_is_patch_error():
    assert issubclass(PointerError, PatchError)


# RFC 6902 Appendix A examples plus per-operation behaviour.

def test_add_object_member():
    doc = {"foo": "bar"}
    out = apply_patch(doc, [{"op": "add", "path": "/baz", "value": "qux"}])
    assert out == {"foo": "bar", "baz": "qux"}


def test_add_array_element_inserts():
    doc = {"foo": ["bar", "baz"]}
    out = apply_patch(doc, [{"op": "add", "path": "/foo/1", "value": "qux"}])
    assert out == {"foo": ["bar", "qux", "baz"]}


def test_add_array_end_with_index_equal_len():
    out = apply_patch({"a": [1, 2]}, [{"op": "add", "path": "/a/2", "value": 3}])
    assert out == {"a": [1, 2, 3]}


def test_add_array_dash_appends():
    out = apply_patch({"a": [1]}, [{"op": "add", "path": "/a/-", "value": 2}])
    assert out == {"a": [1, 2]}


def test_add_replaces_existing_object_member():
    out = apply_patch({"a": 1}, [{"op": "add", "path": "/a", "value": 2}])
    assert out == {"a": 2}


def test_add_array_index_past_end_fails():
    with pytest.raises(PatchError):
        apply_patch({"a": [1]}, [{"op": "add", "path": "/a/2", "value": 3}])


def test_add_root_replaces_document():
    assert apply_patch({"a": 1}, [{"op": "add", "path": "", "value": [1]}]) == [1]


def test_add_missing_parent_fails():
    with pytest.raises(PointerError):
        apply_patch({}, [{"op": "add", "path": "/a/b", "value": 1}])


def test_remove_object_member():
    out = apply_patch({"a": 1, "b": 2}, [{"op": "remove", "path": "/a"}])
    assert out == {"b": 2}


def test_remove_array_element():
    out = apply_patch({"a": [1, 2, 3]}, [{"op": "remove", "path": "/a/1"}])
    assert out == {"a": [1, 3]}


def test_remove_missing_fails():
    with pytest.raises(PointerError):
        apply_patch({"a": 1}, [{"op": "remove", "path": "/b"}])


def test_remove_dash_fails():
    with pytest.raises(PointerError):
        apply_patch({"a": [1]}, [{"op": "remove", "path": "/a/-"}])


def test_remove_root_fails():
    with pytest.raises(PatchError):
        apply_patch({"a": 1}, [{"op": "remove", "path": ""}])


def test_replace_object_member():
    out = apply_patch({"a": 1}, [{"op": "replace", "path": "/a", "value": 2}])
    assert out == {"a": 2}


def test_replace_array_element_overwrites_not_inserts():
    out = apply_patch({"a": [1, 2, 3]}, [{"op": "replace", "path": "/a/1", "value": 9}])
    assert out == {"a": [1, 9, 3]}


def test_replace_missing_fails():
    with pytest.raises(PointerError):
        apply_patch({"a": 1}, [{"op": "replace", "path": "/b", "value": 2}])


def test_replace_root():
    assert apply_patch({"a": 1}, [{"op": "replace", "path": "", "value": "x"}]) == "x"


def test_move_object_member():
    doc = {"foo": {"bar": "baz"}, "qux": {"corge": "grault"}}
    out = apply_patch(doc, [{"op": "move", "from": "/foo/bar", "path": "/qux/thud"}])
    assert out == {"foo": {}, "qux": {"corge": "grault", "thud": "baz"}}


def test_move_array_element():
    doc = {"foo": ["all", "grass", "cows", "eat"]}
    out = apply_patch(doc, [{"op": "move", "from": "/foo/1", "path": "/foo/3"}])
    assert out == {"foo": ["all", "cows", "eat", "grass"]}


def test_move_into_own_child_fails():
    with pytest.raises(PatchError):
        apply_patch({"a": {"b": 1}}, [{"op": "move", "from": "/a", "path": "/a/b/c"}])


def test_move_prefix_check_is_by_segment_not_string():
    # "/ab" is not a child of "/a".
    out = apply_patch({"a": 1, "ab": {}}, [{"op": "move", "from": "/a", "path": "/ab/x"}])
    assert out == {"ab": {"x": 1}}


def test_move_missing_source_fails():
    with pytest.raises(PointerError):
        apply_patch({"a": 1}, [{"op": "move", "from": "/b", "path": "/c"}])


def test_move_to_same_path_is_noop():
    doc = {"a": [1, 2]}
    assert apply_patch(doc, [{"op": "move", "from": "/a/0", "path": "/a/0"}]) == doc


def test_copy_object_member_is_deep():
    doc = {"foo": {"bar": [1]}}
    out = apply_patch(doc, [{"op": "copy", "from": "/foo", "path": "/baz"}])
    assert out == {"foo": {"bar": [1]}, "baz": {"bar": [1]}}
    out["baz"]["bar"].append(2)
    assert out["foo"] == {"bar": [1]}


def test_copy_missing_source_fails():
    with pytest.raises(PointerError):
        apply_patch({}, [{"op": "copy", "from": "/x", "path": "/y"}])


def test_test_passes_and_fails():
    doc = {"baz": "qux", "foo": ["a", 2, "c"]}
    apply_patch(doc, [{"op": "test", "path": "/baz", "value": "qux"}])
    apply_patch(doc, [{"op": "test", "path": "/foo/1", "value": 2}])
    with pytest.raises(PatchError):
        apply_patch(doc, [{"op": "test", "path": "/baz", "value": "bar"}])


def test_test_missing_target_fails():
    with pytest.raises(PointerError):
        apply_patch({}, [{"op": "test", "path": "/x", "value": 1}])


@pytest.mark.parametrize(
    "actual, expected, passes",
    [
        (1, 1.0, True),
        (1.0, 1, True),
        (True, 1, False),
        (1, True, False),
        (False, 0, False),
        (None, None, True),
        (None, 0, False),
        ("1", 1, False),
        ([1, {"a": True}], [1.0, {"a": True}], True),
        ([1, {"a": True}], [1.0, {"a": 1}], False),
        ({"a": [1]}, {"a": [1, 2]}, False),
        ({"a": 1}, {"b": 1}, False),
        ([1], {"0": 1}, False),
    ],
)
def test_test_equality_rules(actual, expected, passes):
    doc = {"v": actual}
    op = [{"op": "test", "path": "/v", "value": expected}]
    if passes:
        assert apply_patch(doc, op) == doc
    else:
        with pytest.raises(PatchError):
            apply_patch(doc, op)


def test_operations_apply_in_order():
    out = apply_patch({}, [
        {"op": "add", "path": "/a", "value": 1},
        {"op": "replace", "path": "/a", "value": 2},
        {"op": "copy", "from": "/a", "path": "/b"},
        {"op": "move", "from": "/a", "path": "/c"},
    ])
    assert out == {"b": 2, "c": 2}


def test_failed_patch_leaves_input_unchanged():
    doc = {"a": [1], "b": {"c": 1}}
    snapshot = copy.deepcopy(doc)
    patch = [
        {"op": "add", "path": "/a/-", "value": 2},
        {"op": "remove", "path": "/b/c"},
        {"op": "test", "path": "/a/0", "value": 99},
    ]
    with pytest.raises(PatchError):
        apply_patch(doc, patch)
    assert doc == snapshot


def test_failed_patch_in_place_leaves_input_unchanged():
    doc = {"a": [1]}
    snapshot = copy.deepcopy(doc)
    with pytest.raises(PatchError):
        apply_patch(doc, [{"op": "add", "path": "/a/-", "value": 2}, {"op": "remove", "path": "/zz"}], in_place=True)
    assert doc == snapshot


def test_input_never_mutated_without_in_place():
    doc = {"a": {"b": [1]}}
    snapshot = copy.deepcopy(doc)
    out = apply_patch(doc, [{"op": "add", "path": "/a/b/-", "value": 2}])
    assert out == {"a": {"b": [1, 2]}}
    assert doc == snapshot
    assert out is not doc


def test_in_place_mutates_dict_and_returns_it():
    doc = {"a": 1}
    out = apply_patch(doc, [{"op": "add", "path": "/b", "value": 2}], in_place=True)
    assert out is doc
    assert doc == {"a": 1, "b": 2}


def test_in_place_mutates_list_and_returns_it():
    doc = [1, 2]
    out = apply_patch(doc, [{"op": "remove", "path": "/0"}], in_place=True)
    assert out is doc
    assert doc == [2]


def test_in_place_root_type_change_returns_new_value():
    doc = {"a": 1}
    out = apply_patch(doc, [{"op": "replace", "path": "", "value": [1]}], in_place=True)
    assert out == [1]


def test_patch_value_not_aliased_into_result():
    value = {"x": []}
    patch = [
        {"op": "add", "path": "/a", "value": value},
        {"op": "add", "path": "/a/x/-", "value": 1},
    ]
    out = apply_patch({}, patch)
    assert out == {"a": {"x": [1]}}
    assert value == {"x": []}


def test_empty_patch_returns_copy():
    doc = {"a": 1}
    out = apply_patch(doc, [])
    assert out == doc and out is not doc


@pytest.mark.parametrize(
    "patch",
    [
        {"op": "add", "path": "/a", "value": 1},  # not a list
        ["add"],  # op not a dict
        [{"path": "/a", "value": 1}],  # missing op
        [{"op": "frobnicate", "path": "/a"}],  # unknown op
        [{"op": "add", "value": 1}],  # missing path
        [{"op": "add", "path": 3, "value": 1}],  # wrong path type
        [{"op": "add", "path": "/a"}],  # add without value
        [{"op": "replace", "path": "/a"}],  # replace without value
        [{"op": "test", "path": "/a"}],  # test without value
        [{"op": "copy", "path": "/a"}],  # copy without from
        [{"op": "move", "path": "/a", "from": 1}],  # wrong from type
    ],
)
def test_malformed_patch_raises_patch_error(patch):
    with pytest.raises(PatchError):
        apply_patch({"a": 1}, patch)


def test_bad_pointer_in_op_raises_patch_error():
    with pytest.raises(PatchError):
        apply_patch({"a": 1}, [{"op": "remove", "path": "a"}])
