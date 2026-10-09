"""Cross-check resolve() against exhaustive enumeration on small random indexes."""

import itertools
import random

import pytest

from resolver.solve import Constraint, ResolutionError, Version, resolve

NAMES = ["a", "b", "c", "d"]
VERSIONS = ["1", "2", "3"]
OPS = ["", "==1", "==2", ">=2", "<3", ">1", "!=2"]


def _random_index(rng):
    index = {}
    for name in NAMES[: rng.randint(2, len(NAMES))]:
        versions = {}
        for v in rng.sample(VERSIONS, rng.randint(1, 3)):
            reqs = []
            for dep in rng.sample(NAMES, rng.randint(0, 2)):
                reqs.append(dep + rng.choice(OPS))
            versions[v] = reqs
        index[name] = versions
    return index


def _valid(assignment, roots, index):
    """Return True if the assignment is a solution for the given roots."""
    present = {n: v for n, v in assignment.items() if v is not None}
    for req in roots:
        c = Constraint.parse(req)
        if c.name not in present or not c.allows(present[c.name]):
            return False
    reached = set()
    stack = [Constraint.parse(r).name for r in roots]
    while stack:
        name = stack.pop()
        if name in reached:
            continue
        reached.add(name)
        if name not in present:
            return False
        for req in index[name][present[name]]:
            c = Constraint.parse(req)
            if c.name not in present or not c.allows(present[c.name]):
                return False
            stack.append(c.name)
    return reached == set(present)


def _brute_force(roots, index):
    names = sorted(index)
    best = None
    best_key = None
    for combo in itertools.product(*[[None, *index[n]] for n in names]):
        assignment = dict(zip(names, combo))
        if not _valid(assignment, roots, index):
            continue
        # Absent sorts below any version. Versions compare numerically.
        key = tuple((0,) if v is None else (1, Version(v)._key) for v in combo)
        if best_key is None or key > best_key:
            best_key = key
            best = {n: v for n, v in assignment.items() if v is not None}
    return best


@pytest.mark.parametrize("seed", range(300))
def test_matches_exhaustive_search(seed):
    rng = random.Random(seed)
    index = _random_index(rng)
    roots = rng.sample(sorted(index), rng.randint(1, min(2, len(index))))
    roots = [r + rng.choice(OPS) for r in roots]
    expected = _brute_force(roots, index)
    if expected is None:
        with pytest.raises(ResolutionError):
            resolve(roots, index)
    else:
        assert resolve(roots, index) == expected
