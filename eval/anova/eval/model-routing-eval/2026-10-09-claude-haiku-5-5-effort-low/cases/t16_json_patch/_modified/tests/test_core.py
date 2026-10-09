import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from jsonpatch.core import PatchError, PointerError, apply_patch, resolve_pointer  # noqa: E402


class ResolvePointerTests(unittest.TestCase):
    def test_empty_pointer_is_whole_document(self):
        doc = {"a": 1}
        self.assertIs(resolve_pointer(doc, ""), doc)

    def test_nested_object_and_array(self):
        doc = {"a": {"b": [10, 20, {"c": "x"}]}}
        self.assertEqual(resolve_pointer(doc, "/a/b/1"), 20)
        self.assertEqual(resolve_pointer(doc, "/a/b/2/c"), "x")

    def test_escapes_unescaped_in_order(self):
        doc = {"a/b": 1, "m~n": 2, "~1": 3}
        self.assertEqual(resolve_pointer(doc, "/a~1b"), 1)
        self.assertEqual(resolve_pointer(doc, "/m~0n"), 2)
        # "~01" must decode to "~1", not "/"
        self.assertEqual(resolve_pointer(doc, "/~01"), 3)

    def test_zero_index_ok_leading_zero_rejected(self):
        doc = [1, 2]
        self.assertEqual(resolve_pointer(doc, "/0"), 1)
        with self.assertRaises(PointerError):
            resolve_pointer(doc, "/01")

    def test_errors(self):
        doc = {"a": [1], "s": "str"}
        for bad in ["a", "/missing", "/a/5", "/a/-", "/a/x", "/s/0", "/a/0/z", "/~2", "/a~"]:
            with self.subTest(pointer=bad), self.assertRaises(PointerError):
                resolve_pointer(doc, bad)

    def test_pointer_error_is_patch_error(self):
        self.assertTrue(issubclass(PointerError, PatchError))


class AddTests(unittest.TestCase):
    def test_add_object_key(self):
        self.assertEqual(apply_patch({}, [{"op": "add", "path": "/a", "value": 1}]), {"a": 1})

    def test_add_array_insert_and_append(self):
        doc = {"l": [1, 3]}
        out = apply_patch(doc, [
            {"op": "add", "path": "/l/1", "value": 2},
            {"op": "add", "path": "/l/-", "value": 4},
        ])
        self.assertEqual(out, {"l": [1, 2, 3, 4]})

    def test_add_index_len_allowed_beyond_rejected(self):
        self.assertEqual(apply_patch([1], [{"op": "add", "path": "/1", "value": 2}]), [1, 2])
        with self.assertRaises(PatchError):
            apply_patch([1], [{"op": "add", "path": "/2", "value": 2}])

    def test_add_root_replaces_document(self):
        self.assertEqual(apply_patch({"a": 1}, [{"op": "add", "path": "", "value": [9]}]), [9])

    def test_add_under_missing_parent_fails(self):
        with self.assertRaises(PointerError):
            apply_patch({}, [{"op": "add", "path": "/a/b", "value": 1}])


class RemoveReplaceTests(unittest.TestCase):
    def test_remove_key_and_index(self):
        self.assertEqual(apply_patch({"a": 1, "b": 2}, [{"op": "remove", "path": "/a"}]), {"b": 2})
        self.assertEqual(apply_patch([1, 2, 3], [{"op": "remove", "path": "/0"}]), [2, 3])

    def test_remove_missing_fails(self):
        with self.assertRaises(PointerError):
            apply_patch({}, [{"op": "remove", "path": "/a"}])
        with self.assertRaises(PointerError):
            apply_patch([1], [{"op": "remove", "path": "/-"}])

    def test_remove_root_fails(self):
        with self.assertRaises(PatchError):
            apply_patch({"a": 1}, [{"op": "remove", "path": ""}])

    def test_replace(self):
        self.assertEqual(apply_patch({"a": 1}, [{"op": "replace", "path": "/a", "value": 2}]), {"a": 2})
        self.assertEqual(apply_patch([1, 2], [{"op": "replace", "path": "/1", "value": 5}]), [1, 5])
        self.assertEqual(apply_patch({"a": 1}, [{"op": "replace", "path": "", "value": "x"}]), "x")

    def test_replace_missing_fails(self):
        with self.assertRaises(PointerError):
            apply_patch({}, [{"op": "replace", "path": "/a", "value": 1}])


class MoveCopyTests(unittest.TestCase):
    def test_move_key(self):
        out = apply_patch({"a": {"x": 1}}, [{"op": "move", "from": "/a/x", "path": "/b"}])
        self.assertEqual(out, {"a": {}, "b": 1})

    def test_move_within_array(self):
        out = apply_patch([1, 2, 3], [{"op": "move", "from": "/0", "path": "/2"}])
        self.assertEqual(out, [2, 3, 1])

    def test_move_into_own_child_fails(self):
        with self.assertRaises(PatchError):
            apply_patch({"a": {"b": 1}}, [{"op": "move", "from": "/a", "path": "/a/b/c"}])
        with self.assertRaises(PatchError):
            apply_patch({"a": 1}, [{"op": "move", "from": "", "path": "/x"}])

    def test_move_prefix_by_string_not_token_is_allowed(self):
        out = apply_patch({"a": 1, "ab": {}}, [{"op": "move", "from": "/a", "path": "/ab/x"}])
        self.assertEqual(out, {"ab": {"x": 1}})

    def test_move_missing_source_fails(self):
        with self.assertRaises(PointerError):
            apply_patch({}, [{"op": "move", "from": "/a", "path": "/b"}])

    def test_copy_is_deep(self):
        doc = {"a": {"l": [1]}}
        out = apply_patch(doc, [{"op": "copy", "from": "/a", "path": "/b"},
                                {"op": "add", "path": "/b/l/-", "value": 2}])
        self.assertEqual(out, {"a": {"l": [1]}, "b": {"l": [1, 2]}})

    def test_copy_missing_source_fails(self):
        with self.assertRaises(PointerError):
            apply_patch({}, [{"op": "copy", "from": "/a", "path": "/b"}])


class TestOpTests(unittest.TestCase):
    def test_pass(self):
        doc = {"a": [1, {"b": None}]}
        self.assertEqual(apply_patch(doc, [{"op": "test", "path": "/a/1/b", "value": None}]), doc)

    def test_fail(self):
        with self.assertRaises(PatchError):
            apply_patch({"a": 1}, [{"op": "test", "path": "/a", "value": 2}])

    def test_numbers_compare_by_value(self):
        apply_patch({"a": 1}, [{"op": "test", "path": "/a", "value": 1.0}])

    def test_bool_is_not_number(self):
        with self.assertRaises(PatchError):
            apply_patch({"a": 1}, [{"op": "test", "path": "/a", "value": True}])
        with self.assertRaises(PatchError):
            apply_patch({"a": True}, [{"op": "test", "path": "/a", "value": 1}])
        with self.assertRaises(PatchError):
            apply_patch({"a": [True]}, [{"op": "test", "path": "/a", "value": [1]}])

    def test_deep_equality(self):
        apply_patch({"a": {"x": [1, 2]}},
                    [{"op": "test", "path": "/a", "value": {"x": [1.0, 2]}}])
        with self.assertRaises(PatchError):
            apply_patch({"a": {"x": [1, 2]}},
                        [{"op": "test", "path": "/a", "value": {"x": [1, 2], "y": 0}}])

    def test_missing_target_fails(self):
        with self.assertRaises(PointerError):
            apply_patch({}, [{"op": "test", "path": "/a", "value": None}])


class AtomicityTests(unittest.TestCase):
    def test_failure_leaves_input_unchanged(self):
        doc = {"a": [1, 2], "b": {"c": 3}}
        snapshot = copy.deepcopy(doc)
        patch = [
            {"op": "add", "path": "/a/-", "value": 9},
            {"op": "replace", "path": "/b/c", "value": 4},
            {"op": "remove", "path": "/missing"},
        ]
        with self.assertRaises(PointerError):
            apply_patch(doc, patch)
        self.assertEqual(doc, snapshot)

    def test_failure_in_place_leaves_input_unchanged(self):
        doc = {"a": 1}
        with self.assertRaises(PatchError):
            apply_patch(doc, [{"op": "replace", "path": "/a", "value": 2},
                              {"op": "test", "path": "/a", "value": 1}], in_place=True)
        self.assertEqual(doc, {"a": 1})

    def test_default_does_not_mutate_input(self):
        doc = {"a": [1]}
        out = apply_patch(doc, [{"op": "add", "path": "/a/-", "value": 2}])
        self.assertEqual(doc, {"a": [1]})
        self.assertEqual(out, {"a": [1, 2]})

    def test_in_place_mutates_on_success(self):
        doc = {"a": [1]}
        out = apply_patch(doc, [{"op": "add", "path": "/a/-", "value": 2}], in_place=True)
        self.assertIs(out, doc)
        self.assertEqual(doc, {"a": [1, 2]})

    def test_in_place_list_root(self):
        doc = [1]
        out = apply_patch(doc, [{"op": "add", "path": "/-", "value": 2}], in_place=True)
        self.assertIs(out, doc)
        self.assertEqual(doc, [1, 2])

    def test_in_place_root_scalar_replace_returns_new(self):
        self.assertEqual(apply_patch(5, [{"op": "replace", "path": "", "value": 6}], in_place=True), 6)

    def test_patch_values_not_aliased(self):
        value = {"x": [1]}
        out = apply_patch({}, [{"op": "add", "path": "/a", "value": value},
                               {"op": "add", "path": "/a/x/-", "value": 2}])
        self.assertEqual(out, {"a": {"x": [1, 2]}})
        self.assertEqual(value, {"x": [1]})


class MalformedPatchTests(unittest.TestCase):
    def test_bad_patch_shapes(self):
        cases = [
            {"op": "add", "path": "/a", "value": 1},  # not a list
            ["add"],
            [{"path": "/a", "value": 1}],
            [{"op": "frobnicate", "path": "/a"}],
            [{"op": ["add"], "path": "/a", "value": 1}],
            [{"op": "add", "value": 1}],
            [{"op": "add", "path": 3, "value": 1}],
            [{"op": "add", "path": "/a"}],
            [{"op": "copy", "path": "/a"}],
            [{"op": "move", "from": 1, "path": "/a"}],
            [{"op": "test", "path": "/a"}],
        ]
        for patch in cases:
            with self.subTest(patch=patch), self.assertRaises(PatchError):
                apply_patch({"a": 1}, patch)


if __name__ == "__main__":
    unittest.main()
