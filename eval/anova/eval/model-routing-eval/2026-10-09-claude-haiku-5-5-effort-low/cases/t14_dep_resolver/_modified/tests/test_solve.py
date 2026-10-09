import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from resolver import Constraint, ResolutionError, Version, resolve  # noqa: E402


SPEC_INDEX = {
    "app": {"1.0": ["web>=2", "db"]},
    "web": {"1.0": [], "2.0": ["json<3"], "2.1": ["json>=3"]},
    "json": {"2.0": [], "3.0": []},
    "db": {"1.0": ["json<3"]},
}


class VersionTests(unittest.TestCase):
    def test_trailing_zeros_equal(self):
        self.assertEqual(Version("1.0"), Version("1"))
        self.assertEqual(hash(Version("1.0")), hash(Version("1")))

    def test_numeric_comparison(self):
        self.assertGreater(Version("1.10"), Version("1.9"))
        self.assertLess(Version("2"), Version("2.0.1"))

    def test_str_preserves_original(self):
        self.assertEqual(str(Version("1.0")), "1.0")

    def test_invalid(self):
        with self.assertRaises(ValueError):
            Version("1.x")


class ConstraintTests(unittest.TestCase):
    def test_parse_bare_name(self):
        c = Constraint.parse("web")
        self.assertEqual(c.name, "web")
        self.assertTrue(c.allows(Version("0.1")))

    def test_parse_range(self):
        c = Constraint.parse("json>=2,<3")
        self.assertEqual(c.name, "json")
        self.assertTrue(c.allows(Version("2")))
        self.assertTrue(c.allows(Version("2.9")))
        self.assertFalse(c.allows(Version("3")))
        self.assertFalse(c.allows(Version("1.9")))

    def test_all_operators(self):
        self.assertTrue(Constraint.parse("db==1.0").allows(Version("1")))
        self.assertFalse(Constraint.parse("db==1.0").allows(Version("1.1")))
        self.assertFalse(Constraint.parse("db!=1.0").allows(Version("1")))
        self.assertTrue(Constraint.parse("db<=1.0").allows(Version("1")))
        self.assertFalse(Constraint.parse("db>1.0").allows(Version("1")))

    def test_invalid_requirement(self):
        with self.assertRaises(ValueError):
            Constraint.parse("json>=")
        with self.assertRaises(ValueError):
            Constraint.parse("json~2")


class ResolveTests(unittest.TestCase):
    def test_spec_example(self):
        # app needs web>=2 (so 2.1 is preferred, which needs json>=3), and db (which needs json<3).
        # json is the conflict, so web must drop to 2.0.
        result = resolve(["app"], SPEC_INDEX)
        self.assertEqual(result, {"app": "1.0", "db": "1.0", "web": "2.0", "json": "2.0"})

    def test_highest_version_preferred(self):
        index = {"a": {"1.0": [], "2.0": [], "3.0": []}}
        self.assertEqual(resolve(["a"], index), {"a": "3.0"})

    def test_alphabetical_preference(self):
        # "a" is decided first, so it gets its highest version (2.0) even though that forces "b" to 3.0.
        # With "a" at 1.0, "b" would be limited to <2 and the result would differ.
        index = {
            "a": {"1.0": ["b<2"], "2.0": ["b>=2"]},
            "b": {"1.0": [], "2.0": [], "3.0": []},
        }
        result = resolve(["a", "b"], index)
        self.assertEqual(result, {"a": "2.0", "b": "3.0"})

    def test_backtracking(self):
        # "leaf" sorts before "mid", so it is decided first and takes 2.0. Both picks are then valid.
        index = {
            "top": {"1.0": ["mid", "leaf"]},
            "mid": {"2.0": ["leaf>=2"], "1.0": ["leaf<2"]},
            "leaf": {"1.0": [], "2.0": []},
        }
        result = resolve(["top"], index)
        self.assertEqual(result, {"top": "1.0", "mid": "2.0", "leaf": "2.0"})

    def test_backtracking_forced(self):
        # "leaf" must drop to 1.0 once "mid" forces it below 2, so "mid" must back off to 1.0.
        index = {
            "top": {"1.0": ["mid", "leaf"]},
            "mid": {"2.0": ["leaf>=2"], "1.0": ["leaf<2"]},
            "leaf": {"1.0": [], "2.0": []},
        }
        index["top"]["1.0"] = ["mid", "leaf<2"]
        result = resolve(["top"], index)
        self.assertEqual(result, {"top": "1.0", "mid": "1.0", "leaf": "1.0"})

    def test_cycle_tolerated(self):
        index = {
            "a": {"1.0": ["b"]},
            "b": {"1.0": ["a"]},
        }
        self.assertEqual(resolve(["a"], index), {"a": "1.0", "b": "1.0"})

    def test_cycle_with_constraint(self):
        index = {
            "a": {"1.0": ["b>=2"], "2.0": ["b<2"]},
            "b": {"1.0": ["a"], "2.0": ["a"]},
        }
        # a 2.0 needs b<2, so b drops to 1.0 even though b 2.0 would be preferred otherwise.
        result = resolve(["a"], index)
        self.assertEqual(result, {"a": "2.0", "b": "1.0"})

    def test_unreachable_packages_excluded(self):
        index = {
            "a": {"1.0": []},
            "unused": {"1.0": ["a"]},
        }
        self.assertEqual(resolve(["a"], index), {"a": "1.0"})

    def test_root_with_constraint(self):
        index = {"a": {"1.0": [], "2.0": [], "3.0": []}}
        self.assertEqual(resolve(["a<3"], index), {"a": "2.0"})

    def test_unsatisfiable_names_leaf(self):
        index = {
            "a": {"1.0": ["b<1"]},
            "b": {"1.0": [], "2.0": []},
        }
        with self.assertRaises(ResolutionError) as ctx:
            resolve(["a"], index)
        self.assertIn("'b'", str(ctx.exception))

    def test_unsatisfiable_root_names_root(self):
        index = {"a": {"1.0": []}}
        with self.assertRaises(ResolutionError) as ctx:
            resolve(["a>=2"], index)
        self.assertIn("'a'", str(ctx.exception))

    def test_missing_package(self):
        with self.assertRaises(ResolutionError) as ctx:
            resolve(["ghost"], {})
        self.assertIn("'ghost'", str(ctx.exception))

    def test_large_index_is_fast(self):
        # Many versions per package with a conflict that only resolves at the bottom of the chain.
        n_layers, n_versions = 6, 200
        index = {}
        for layer in range(n_layers):
            name = f"p{layer}"
            versions = {}
            for v in range(1, n_versions + 1):
                reqs = []
                if layer + 1 < n_layers:
                    reqs.append(f"p{layer + 1}")
                versions[f"{v}.0"] = reqs
            index[name] = versions
        index["p%d" % (n_layers - 1)] = {f"{v}.0": [] for v in range(1, n_versions + 1)}
        index["p0"]["1.0"] = []
        index["pz"] = {"1.0": ["p0<2"], "2.0": ["p0<2"]}
        index["root"] = {"1.0": ["pz", "p%d>=%d" % (n_layers - 1, n_versions)]}
        start = time.time()
        result = resolve(["root"], index)
        self.assertLess(time.time() - start, 10)
        self.assertEqual(result["p%d" % (n_layers - 1)], f"{n_versions}.0")


if __name__ == "__main__":
    unittest.main()
