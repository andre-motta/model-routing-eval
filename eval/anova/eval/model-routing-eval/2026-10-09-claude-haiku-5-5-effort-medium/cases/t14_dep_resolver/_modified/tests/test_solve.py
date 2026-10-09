import itertools
import random
import time
import unittest

from resolver.solve import Constraint, ResolutionError, Version, resolve


SPEC_INDEX = {
    "app": {"1.0": ["web>=2", "db"]},
    "web": {"1.0": [], "2.0": ["json<3"], "2.1": ["json>=3"]},
    "json": {"2.0": [], "3.0": []},
    "db": {"1.0": ["json<3"]},
}


def _valid(chosen, roots, index):
    """Return True if `chosen` (name -> version string) is a valid, reachable solution."""
    def satisfied(req, chosen):
        c = Constraint.parse(req)
        return c.name in chosen and c.allows(Version(chosen[c.name]))

    if not all(satisfied(r, chosen) for r in roots):
        return False
    reachable, frontier = set(), [Constraint.parse(r).name for r in roots]
    while frontier:
        name = frontier.pop()
        if name in reachable:
            continue
        reachable.add(name)
        if name not in chosen or chosen[name] not in index.get(name, {}):
            return False
        for req in index[name][chosen[name]]:
            if not satisfied(req, chosen):
                return False
            frontier.append(Constraint.parse(req).name)
    return reachable == set(chosen)


def _brute_force(roots, index):
    """All valid solutions, found by trying every choice of version (or absence) per package."""
    names = sorted(index)
    options = [[None] + list(index[n]) for n in names]
    found = []
    for combo in itertools.product(*options):
        chosen = {n: v for n, v in zip(names, combo) if v is not None}
        if _valid(chosen, roots, index):
            found.append(chosen)
    return found


def _key(chosen):
    return [(name, Version(chosen[name])) for name in sorted(chosen)]


class VersionTests(unittest.TestCase):
    def test_missing_components_are_zero(self):
        self.assertEqual(Version("1.0"), Version("1"))
        self.assertEqual(hash(Version("1.0")), hash(Version("1")))
        self.assertEqual(Version("1.0.0"), Version("1"))

    def test_numeric_not_lexical_comparison(self):
        self.assertGreater(Version("1.10"), Version("1.9"))
        self.assertLess(Version("1.9"), Version("1.10"))
        self.assertLess(Version("1"), Version("1.0.1"))

    def test_str_keeps_original_text(self):
        self.assertEqual(str(Version("1.10")), "1.10")
        self.assertEqual(str(Version("2")), "2")

    def test_invalid_version_rejected(self):
        with self.assertRaises(ValueError):
            Version("1.x")


class ConstraintTests(unittest.TestCase):
    def test_parse_bare_name(self):
        c = Constraint.parse("web")
        self.assertEqual(c.name, "web")
        self.assertTrue(c.allows(Version("0.1")))

    def test_parse_compound(self):
        c = Constraint.parse("json>=2,<3")
        self.assertEqual(c.name, "json")
        self.assertTrue(c.allows(Version("2")))
        self.assertTrue(c.allows(Version("2.9.9")))
        self.assertFalse(c.allows(Version("3")))
        self.assertFalse(c.allows(Version("1.9")))

    def test_equality_and_inequality_ops(self):
        self.assertTrue(Constraint.parse("db==1.0").allows(Version("1")))
        self.assertFalse(Constraint.parse("db==1.0").allows(Version("1.1")))
        self.assertFalse(Constraint.parse("db!=1.0").allows(Version("1.0")))
        self.assertTrue(Constraint.parse("db!=1.0").allows(Version("2")))

    def test_whitespace_tolerated(self):
        c = Constraint.parse(" json >= 2 , < 3 ")
        self.assertEqual(c.name, "json")
        self.assertTrue(c.allows(Version("2.5")))
        self.assertFalse(c.allows(Version("3")))

    def test_invalid_requirement_rejected(self):
        with self.assertRaises(ValueError):
            Constraint.parse("json>=")
        with self.assertRaises(ValueError):
            Constraint.parse("json 2")


class ResolveTests(unittest.TestCase):
    def test_spec_example(self):
        self.assertEqual(
            resolve(["app"], SPEC_INDEX),
            {"app": "1.0", "db": "1.0", "json": "2.0", "web": "2.0"},
        )

    def test_highest_version_preferred(self):
        index = {"a": {"1.0": [], "1.5": [], "1.2": []}}
        self.assertEqual(resolve(["a"], index), {"a": "1.5"})

    def test_root_constraint_applies(self):
        index = {"a": {"1.0": [], "2.0": [], "3.0": []}}
        self.assertEqual(resolve(["a<3"], index), {"a": "2.0"})

    def test_dependencies_pulled_in_transitively(self):
        index = {
            "a": {"1.0": ["b"]},
            "b": {"1.0": ["c>=1"]},
            "c": {"1.0": [], "2.0": []},
        }
        self.assertEqual(resolve(["a"], index), {"a": "1.0", "b": "1.0", "c": "2.0"})

    def test_unreachable_packages_excluded(self):
        index = {
            "a": {"1.0": []},
            "orphan": {"1.0": ["a"]},
        }
        self.assertEqual(resolve(["a"], index), {"a": "1.0"})

    def test_cycle_is_tolerated(self):
        index = {
            "a": {"1.0": ["b"]},
            "b": {"1.0": ["a>=1"]},
        }
        self.assertEqual(resolve(["a"], index), {"a": "1.0", "b": "1.0"})

    def test_self_dependency_is_tolerated(self):
        index = {"a": {"1.0": ["a>=1"], "2.0": ["a"]}}
        self.assertEqual(resolve(["a"], index), {"a": "2.0"})

    def test_cycle_with_conflict_backtracks(self):
        index = {
            "a": {"1.0": ["b"], "2.0": ["b", "c"]},
            "b": {"1.0": ["a==1.0"], "2.0": ["a>=1"]},
            "c": {"1.0": ["a==1.0"]},
        }
        # a 2.0 needs c, which needs a==1.0, so a 1.0 is the only consistent choice.
        self.assertEqual(resolve(["a"], index), {"a": "1.0", "b": "2.0"})

    def test_backtracks_out_of_a_dead_end(self):
        index = {
            "app": {"1.0": ["x", "y"]},
            "x": {"2.0": ["z==2"], "1.0": ["z==1"]},
            "y": {"1.0": ["z==1"]},
            "z": {"1.0": [], "2.0": []},
        }
        self.assertEqual(
            resolve(["app"], index),
            {"app": "1.0", "x": "1.0", "y": "1.0", "z": "1.0"},
        )

    def test_missing_root_raises_naming_it(self):
        with self.assertRaises(ResolutionError) as ctx:
            resolve(["ghost"], SPEC_INDEX)
        self.assertIn("ghost", str(ctx.exception))

    def test_error_names_dead_end_leaf_not_root(self):
        index = {
            "a": {"1.0": ["b<1"]},
            "b": {"1": [], "2": []},
        }
        with self.assertRaises(ResolutionError) as ctx:
            resolve(["a"], index)
        self.assertIn("'b'", str(ctx.exception))
        self.assertNotIn("'a'", str(ctx.exception))

    def test_conflicting_roots_raise(self):
        index = {"a": {"1.0": [], "2.0": []}}
        with self.assertRaises(ResolutionError):
            resolve(["a>=2", "a<2"], index)

    def test_empty_roots(self):
        self.assertEqual(resolve([], SPEC_INDEX), {})

    def test_large_index_completes_quickly(self):
        # 300 versions of `lib`, each demanding a `core` version that the next
        # `lib` version rules out; only a narrow band of `lib` is consistent.
        index = {
            "app": {"1.0": ["lib", "core>=5"]},
            "core": {str(i): [] for i in range(1, 11)},
            "lib": {},
        }
        for i in range(1, 301):
            index["lib"][f"1.{i}"] = [f"core<={i % 4 + 1}"]
        start = time.monotonic()
        with self.assertRaises(ResolutionError):
            resolve(["app"], index)
        self.assertLess(time.monotonic() - start, 10)

    def test_large_index_finds_solution(self):
        index = {
            "app": {"1.0": ["lib", "core>=5"]},
            "core": {str(i): [] for i in range(1, 11)},
            "lib": {},
        }
        for i in range(1, 301):
            index["lib"][f"1.{i}"] = [f"core>={i % 9 + 1}"]
        start = time.monotonic()
        result = resolve(["app"], index)
        self.assertLess(time.monotonic() - start, 10)
        self.assertEqual(result["app"], "1.0")
        # lib 1.300 needs core>=4 and app needs core>=5, so core 10 is the highest core that fits.
        self.assertEqual(result, {"app": "1.0", "core": "10", "lib": "1.300"})
        self.assertTrue(_valid(result, ["app"], index))


class RandomCrossCheckTests(unittest.TestCase):
    def test_matches_brute_force(self):
        rng = random.Random(1234)
        names = ["a", "b", "c", "d"]
        for trial in range(300):
            index = {}
            for name in names:
                versions = {}
                for v in rng.sample(["1", "2", "3", "1.0", "2.5"], rng.randint(1, 3)):
                    reqs = []
                    for dep in rng.sample(names, rng.randint(0, 2)):
                        op = rng.choice(["", "==", ">=", "<", "!="])
                        bound = rng.choice(["1", "2", "3"])
                        reqs.append(dep if op == "" else f"{dep}{op}{bound}")
                    versions[v] = reqs
                index[name] = versions
            roots = rng.sample(names, rng.randint(1, 2))
            solutions = _brute_force(roots, index)
            if not solutions:
                with self.assertRaises(ResolutionError, msg=f"trial {trial}"):
                    resolve(roots, index)
                continue
            result = resolve(roots, index)
            self.assertTrue(_valid(result, roots, index), f"trial {trial}: {result}")
            # No valid solution with the same package set may be lexicographically greater.
            same_set = [s for s in solutions if set(s) == set(result)]
            for other in same_set:
                self.assertLessEqual(_key(other), _key(result), f"trial {trial}")


if __name__ == "__main__":
    unittest.main()
