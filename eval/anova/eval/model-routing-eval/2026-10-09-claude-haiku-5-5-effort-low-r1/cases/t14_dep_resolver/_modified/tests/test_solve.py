import os
import sys
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from resolver.solve import Constraint, ResolutionError, Version, resolve  # noqa: E402


EXAMPLE_INDEX = {
    "app": {"1.0": ["web>=2", "db"]},
    "web": {"1.0": [], "2.0": ["json<3"], "2.1": ["json>=3"]},
    "json": {"2.0": [], "3.0": []},
    "db": {"1.0": ["json<3"]},
}


class VersionTests(unittest.TestCase):
    def test_numeric_comparison(self):
        self.assertLess(Version("1.9"), Version("1.10"))
        self.assertGreater(Version("1.10"), Version("1.9"))

    def test_missing_components_are_zero(self):
        self.assertEqual(Version("1.0"), Version("1"))
        self.assertEqual(hash(Version("1.0")), hash(Version("1")))
        self.assertGreater(Version("1.0.1"), Version("1"))

    def test_str_keeps_original(self):
        self.assertEqual(str(Version("1.0")), "1.0")

    def test_invalid_version_raises(self):
        with self.assertRaises(ValueError):
            Version("1.a")


class ConstraintTests(unittest.TestCase):
    def test_parse_bare_name(self):
        c = Constraint.parse("web")
        self.assertEqual(c.name, "web")
        self.assertTrue(c.allows(Version("0.1")))

    def test_range(self):
        c = Constraint.parse("json>=2,<3")
        self.assertEqual(c.name, "json")
        self.assertTrue(c.allows(Version("2")))
        self.assertTrue(c.allows(Version("2.9")))
        self.assertFalse(c.allows(Version("3")))
        self.assertFalse(c.allows(Version("1.9")))

    def test_equality_and_not_equal(self):
        self.assertTrue(Constraint.parse("db==1.0").allows(Version("1")))
        self.assertFalse(Constraint.parse("db!=1.0").allows(Version("1")))

    def test_name_with_dash_and_dot(self):
        c = Constraint.parse("my-pkg.x>=1")
        self.assertEqual(c.name, "my-pkg.x")

    def test_invalid_requirement(self):
        with self.assertRaises(ValueError):
            Constraint.parse("web>=")


class ResolveTests(unittest.TestCase):
    def test_spec_example(self):
        result = resolve(["app"], EXAMPLE_INDEX)
        # app needs web>=2 and db; db needs json<3, so json must be 2.0.
        # web 2.1 needs json>=3, so web must be 2.0.
        self.assertEqual(result, {"app": "1.0", "web": "2.0", "db": "1.0", "json": "2.0"})

    def test_highest_version_preferred(self):
        index = {"a": {"1.0": [], "2.0": [], "1.5": []}}
        self.assertEqual(resolve(["a"], index), {"a": "2.0"})

    def test_numeric_not_lexical_order(self):
        index = {"a": {"1.9": [], "1.10": []}}
        self.assertEqual(resolve(["a"], index), {"a": "1.10"})

    def test_root_constraint(self):
        index = {"a": {"1.0": [], "2.0": [], "3.0": []}}
        self.assertEqual(resolve(["a<3"], index), {"a": "2.0"})

    def test_alphabetical_priority(self):
        # Without preference for "a", b could be 2.0 only if a takes 1.0.
        index = {
            "a": {"1.0": ["b"], "2.0": ["b<2"]},
            "b": {"1.0": [], "2.0": []},
        }
        # a gets highest possible: 2.0 requires b<2, so a=2.0, b=1.0.
        self.assertEqual(resolve(["a", "b"], index), {"a": "2.0", "b": "1.0"})

    def test_backtracking(self):
        index = {
            "a": {"2.0": ["b"], "1.0": []},
            "b": {"1.0": [], "2.0": ["c==1"]},
            "c": {"1.0": [], "2.0": []},
            "d": {"1.0": ["c>=2"]},
        }
        # Trying b=2.0 forces c==1, which conflicts with d needing c>=2,
        # so the solver must back off to b=1.0 and then c=2.0.
        result = resolve(["a", "d"], index)
        self.assertEqual(result, {"a": "2.0", "b": "1.0", "c": "2.0", "d": "1.0"})

    def test_unreachable_not_included(self):
        index = {"a": {"1.0": []}, "z": {"1.0": ["a"]}}
        self.assertEqual(resolve(["a"], index), {"a": "1.0"})

    def test_cycle(self):
        index = {
            "a": {"1.0": ["b"]},
            "b": {"1.0": ["a"], "2.0": ["a>=1"]},
        }
        result = resolve(["a"], index)
        self.assertEqual(result, {"a": "1.0", "b": "2.0"})

    def test_self_cycle(self):
        index = {"a": {"1.0": ["a>=1"]}}
        self.assertEqual(resolve(["a"], index), {"a": "1.0"})

    def test_unsatisfiable_names_leaf(self):
        index = {
            "a": {"1.0": ["b<1"]},
            "b": {"1": [], "2": []},
        }
        with self.assertRaises(ResolutionError) as ctx:
            resolve(["a"], index)
        self.assertIn("'b'", str(ctx.exception))

    def test_conflict_between_two_requirers(self):
        index = {
            "a": {"1.0": ["c>=2"]},
            "b": {"1.0": ["c<2"]},
            "c": {"1.0": [], "2.0": []},
        }
        with self.assertRaises(ResolutionError):
            resolve(["a", "b"], index)

    def test_missing_package(self):
        with self.assertRaises(ResolutionError) as ctx:
            resolve(["nope"], {})
        self.assertIn("nope", str(ctx.exception))

    def test_large_index_is_fast(self):
        # Many versions per package; a naive product over all packages would
        # be far too slow, but backtracking with pruning finishes quickly.
        n = 8
        index = {"p0": {f"{i}.0": [f"p1>={i}"] for i in range(300)}}
        for k in range(1, n):
            index[f"p{k}"] = {f"{i}.0": [] for i in range(300)}
        start = time.time()
        result = resolve(["p0"], index)
        self.assertLess(time.time() - start, 10)
        self.assertEqual(result["p0"], "299.0")
        self.assertEqual(result["p1"], "299.0")


if __name__ == "__main__":
    unittest.main()
