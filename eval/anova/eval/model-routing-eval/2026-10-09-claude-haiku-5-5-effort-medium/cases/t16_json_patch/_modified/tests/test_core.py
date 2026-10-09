import copy
import unittest

from jsonpatch import PatchError, PointerError, apply_patch, resolve_pointer


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


class ResolvePointerTests(unittest.TestCase):
    def test_empty_pointer_is_whole_document(self):
        self.assertIs(resolve_pointer(DOC, ""), DOC)

    def test_rfc6901_examples(self):
        self.assertEqual(resolve_pointer(DOC, "/foo"), ["bar", "baz"])
        self.assertEqual(resolve_pointer(DOC, "/foo/0"), "bar")
        self.assertEqual(resolve_pointer(DOC, "/"), 0)
        self.assertEqual(resolve_pointer(DOC, "/a~1b"), 1)
        self.assertEqual(resolve_pointer(DOC, "/c%d"), 2)
        self.assertEqual(resolve_pointer(DOC, "/e^f"), 3)
        self.assertEqual(resolve_pointer(DOC, "/g|h"), 4)
        self.assertEqual(resolve_pointer(DOC, "/i\\j"), 5)
        self.assertEqual(resolve_pointer(DOC, '/k"l'), 6)
        self.assertEqual(resolve_pointer(DOC, "/ "), 7)
        self.assertEqual(resolve_pointer(DOC, "/m~0n"), 8)

    def test_unescape_order(self):
        doc = {"~1": "tilde-one", "~": "tilde-zero", "/": "slash"}
        self.assertEqual(resolve_pointer(doc, "/~01"), "tilde-one")
        self.assertEqual(resolve_pointer(doc, "/~0"), "tilde-zero")
        self.assertEqual(resolve_pointer(doc, "/~1"), "slash")

    def test_array_index_rules(self):
        doc = {"xs": [10, 20, 30]}
        self.assertEqual(resolve_pointer(doc, "/xs/0"), 10)
        self.assertEqual(resolve_pointer(doc, "/xs/2"), 30)
        for bad in ("01", "-", "+1", "1.0", " 1", "", "3", "99999999999999999999"):
            with self.subTest(token=bad):
                with self.assertRaises(PointerError):
                    resolve_pointer(doc, "/xs/" + bad)

    def test_missing_and_invalid_pointers_raise(self):
        with self.assertRaises(PointerError):
            resolve_pointer(DOC, "/missing")
        with self.assertRaises(PointerError):
            resolve_pointer(DOC, "/foo/0/deeper")
        with self.assertRaises(PointerError):
            resolve_pointer(DOC, "foo")
        with self.assertRaises(PointerError):
            resolve_pointer(DOC, None)

    def test_pointer_errors_are_patch_errors(self):
        self.assertTrue(issubclass(PointerError, PatchError))


class ApplyPatchTests(unittest.TestCase):
    def test_add_object_key(self):
        self.assertEqual(apply_patch({"a": 1}, [{"op": "add", "path": "/b", "value": 2}]),
                         {"a": 1, "b": 2})

    def test_add_overwrites_existing_object_key(self):
        self.assertEqual(apply_patch({"a": 1}, [{"op": "add", "path": "/a", "value": 9}]),
                         {"a": 9})

    def test_add_array_insert_middle_end_and_append(self):
        doc = {"xs": [1, 2, 3]}
        self.assertEqual(apply_patch(doc, [{"op": "add", "path": "/xs/1", "value": "x"}]),
                         {"xs": [1, "x", 2, 3]})
        self.assertEqual(apply_patch(doc, [{"op": "add", "path": "/xs/3", "value": 4}]),
                         {"xs": [1, 2, 3, 4]})
        self.assertEqual(apply_patch(doc, [{"op": "add", "path": "/xs/-", "value": 4}]),
                         {"xs": [1, 2, 3, 4]})

    def test_add_array_index_past_end_fails(self):
        with self.assertRaises(PatchError):
            apply_patch({"xs": [1]}, [{"op": "add", "path": "/xs/2", "value": 0}])

    def test_add_to_missing_parent_fails(self):
        with self.assertRaises(PatchError):
            apply_patch({}, [{"op": "add", "path": "/a/b", "value": 0}])

    def test_add_root_replaces_document(self):
        self.assertEqual(apply_patch({"a": 1}, [{"op": "add", "path": "", "value": [1]}]), [1])

    def test_remove_object_and_array_elements(self):
        self.assertEqual(apply_patch({"a": 1, "b": 2}, [{"op": "remove", "path": "/a"}]),
                         {"b": 2})
        self.assertEqual(apply_patch({"xs": [1, 2, 3]}, [{"op": "remove", "path": "/xs/0"}]),
                         {"xs": [2, 3]})

    def test_remove_missing_target_fails(self):
        with self.assertRaises(PatchError):
            apply_patch({"a": 1}, [{"op": "remove", "path": "/b"}])
        with self.assertRaises(PatchError):
            apply_patch({"xs": []}, [{"op": "remove", "path": "/xs/0"}])

    def test_remove_root_fails(self):
        with self.assertRaises(PatchError):
            apply_patch({"a": 1}, [{"op": "remove", "path": ""}])

    def test_replace_existing_target(self):
        self.assertEqual(apply_patch({"a": 1}, [{"op": "replace", "path": "/a", "value": 2}]),
                         {"a": 2})
        self.assertEqual(apply_patch({"xs": [1, 2]}, [{"op": "replace", "path": "/xs/1", "value": 5}]),
                         {"xs": [1, 5]})

    def test_replace_root(self):
        self.assertEqual(apply_patch({"a": 1}, [{"op": "replace", "path": "", "value": "s"}]), "s")

    def test_replace_missing_target_fails(self):
        with self.assertRaises(PatchError):
            apply_patch({"a": 1}, [{"op": "replace", "path": "/b", "value": 2}])
        with self.assertRaises(PatchError):
            apply_patch({"xs": [1]}, [{"op": "replace", "path": "/xs/1", "value": 2}])

    def test_move_between_keys(self):
        self.assertEqual(
            apply_patch({"a": {"v": 1}, "b": {}}, [{"op": "move", "from": "/a/v", "path": "/b/w"}]),
            {"a": {}, "b": {"w": 1}},
        )

    def test_move_within_array_uses_remove_then_add(self):
        self.assertEqual(
            apply_patch({"xs": [1, 2, 3]}, [{"op": "move", "from": "/xs/0", "path": "/xs/2"}]),
            {"xs": [2, 3, 1]},
        )

    def test_move_to_same_location_is_noop(self):
        doc = {"a": {"b": 1}}
        self.assertEqual(apply_patch(doc, [{"op": "move", "from": "/a", "path": "/a"}]), doc)

    def test_move_into_own_child_fails(self):
        doc = {"a": {"b": {}}}
        with self.assertRaises(PatchError):
            apply_patch(doc, [{"op": "move", "from": "/a", "path": "/a/b/c"}])
        with self.assertRaises(PatchError):
            apply_patch({"a": 1}, [{"op": "move", "from": "", "path": "/x"}])

    def test_move_missing_source_fails(self):
        with self.assertRaises(PatchError):
            apply_patch({"a": 1}, [{"op": "move", "from": "/b", "path": "/c"}])

    def test_copy_is_deep(self):
        result = apply_patch({"a": {"v": [1]}}, [{"op": "copy", "from": "/a", "path": "/b"}])
        self.assertEqual(result, {"a": {"v": [1]}, "b": {"v": [1]}})
        result["b"]["v"].append(2)
        self.assertEqual(result["a"], {"v": [1]})

    def test_copy_missing_source_fails(self):
        with self.assertRaises(PatchError):
            apply_patch({"a": 1}, [{"op": "copy", "from": "/b", "path": "/c"}])

    def test_test_op_passes_and_fails(self):
        doc = {"a": [1, {"b": "x"}]}
        apply_patch(doc, [{"op": "test", "path": "/a", "value": [1, {"b": "x"}]}])
        with self.assertRaises(PatchError):
            apply_patch(doc, [{"op": "test", "path": "/a", "value": [1]}])

    def test_test_op_numbers_compare_by_value(self):
        apply_patch({"n": 1}, [{"op": "test", "path": "/n", "value": 1.0}])
        apply_patch({"n": 1.0}, [{"op": "test", "path": "/n", "value": 1}])

    def test_test_op_bool_is_not_number(self):
        with self.assertRaises(PatchError):
            apply_patch({"b": True}, [{"op": "test", "path": "/b", "value": 1}])
        with self.assertRaises(PatchError):
            apply_patch({"n": 1}, [{"op": "test", "path": "/n", "value": True}])
        with self.assertRaises(PatchError):
            apply_patch({"b": False}, [{"op": "test", "path": "/b", "value": 0}])
        with self.assertRaises(PatchError):
            apply_patch({"xs": [True]}, [{"op": "test", "path": "/xs", "value": [1]}])

    def test_test_op_null_and_missing(self):
        apply_patch({"a": None}, [{"op": "test", "path": "/a", "value": None}])
        with self.assertRaises(PatchError):
            apply_patch({"a": None}, [{"op": "test", "path": "/a", "value": 0}])
        with self.assertRaises(PatchError):
            apply_patch({}, [{"op": "test", "path": "/a", "value": None}])

    def test_test_op_dict_key_order_ignored(self):
        apply_patch({"a": {"x": 1, "y": 2}}, [{"op": "test", "path": "/a", "value": {"y": 2, "x": 1}}])

    def test_operations_apply_in_order(self):
        patch = [
            {"op": "add", "path": "/tmp", "value": 1},
            {"op": "move", "from": "/tmp", "path": "/final"},
        ]
        self.assertEqual(apply_patch({}, patch), {"final": 1})

    def test_input_is_not_mutated_by_default(self):
        doc = {"a": [1, 2], "b": {"c": 3}}
        snapshot = copy.deepcopy(doc)
        result = apply_patch(doc, [
            {"op": "add", "path": "/a/-", "value": 9},
            {"op": "remove", "path": "/b/c"},
        ])
        self.assertEqual(doc, snapshot)
        self.assertEqual(result, {"a": [1, 2, 9], "b": {}})

    def test_output_does_not_alias_patch_values(self):
        value = {"nested": [1]}
        result = apply_patch({}, [{"op": "add", "path": "/v", "value": value}])
        result["v"]["nested"].append(2)
        self.assertEqual(value, {"nested": [1]})

    def test_failure_is_atomic(self):
        doc = {"a": 1}
        snapshot = copy.deepcopy(doc)
        patch = [
            {"op": "add", "path": "/b", "value": 2},
            {"op": "remove", "path": "/missing"},
        ]
        with self.assertRaises(PatchError):
            apply_patch(doc, patch)
        self.assertEqual(doc, snapshot)

    def test_failure_is_atomic_in_place(self):
        doc = {"a": [1]}
        snapshot = copy.deepcopy(doc)
        with self.assertRaises(PatchError):
            apply_patch(doc, [
                {"op": "replace", "path": "/a/0", "value": 2},
                {"op": "test", "path": "/a/0", "value": 3},
            ], in_place=True)
        self.assertEqual(doc, snapshot)

    def test_in_place_mutates_on_success(self):
        doc = {"a": 1}
        result = apply_patch(doc, [{"op": "add", "path": "/b", "value": 2}], in_place=True)
        self.assertIs(result, doc)
        self.assertEqual(doc, {"a": 1, "b": 2})

    def test_in_place_list_root(self):
        doc = [1, 2]
        result = apply_patch(doc, [{"op": "remove", "path": "/0"}], in_place=True)
        self.assertIs(result, doc)
        self.assertEqual(doc, [2])

    def test_unknown_op_fails(self):
        with self.assertRaises(PatchError):
            apply_patch({}, [{"op": "frobnicate", "path": "/a"}])
        with self.assertRaises(PatchError):
            apply_patch({}, [{"path": "/a", "value": 1}])

    def test_missing_or_wrong_fields_fail(self):
        bad_ops = [
            {"op": "add", "path": "/a"},
            {"op": "replace", "path": "/a"},
            {"op": "test", "path": "/a"},
            {"op": "move", "path": "/a"},
            {"op": "copy", "path": "/a", "from": 3},
            {"op": "remove"},
            {"op": "remove", "path": 5},
            {"op": ["add"], "path": "/a", "value": 1},
            "add /a",
        ]
        for op in bad_ops:
            with self.subTest(op=op):
                with self.assertRaises(PatchError):
                    apply_patch({"a": 1}, [op])

    def test_patch_must_be_list(self):
        with self.assertRaises(PatchError):
            apply_patch({}, {"op": "add", "path": "/a", "value": 1})

    def test_null_value_is_allowed(self):
        self.assertEqual(apply_patch({}, [{"op": "add", "path": "/a", "value": None}]), {"a": None})

    def test_empty_patch_returns_copy(self):
        doc = {"a": [1]}
        result = apply_patch(doc, [])
        self.assertEqual(result, doc)
        self.assertIsNot(result, doc)


if __name__ == "__main__":
    unittest.main()
