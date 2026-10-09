import operator
import re
from functools import total_ordering


class ResolutionError(Exception):
    pass


_VERSION_RE = re.compile(r"\d+(\.\d+)*")
_REQ_RE = re.compile(r"\s*([^=!<>,\s]+)\s*(.*)", re.DOTALL)
_SPEC_RE = re.compile(r"(==|!=|<=|>=|<|>)\s*(\S+)")
_OPS = {
    "==": operator.eq,
    "!=": operator.ne,
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
}


@total_ordering
class Version:
    def __init__(self, s):
        text = str(s)
        if not _VERSION_RE.fullmatch(text):
            raise ValueError(f"invalid version: {text!r}")
        self._text = text
        parts = [int(p) for p in text.split(".")]
        # Missing trailing components count as zero, so "1.0" and "1" compare equal.
        while parts and parts[-1] == 0:
            parts.pop()
        self._key = tuple(parts)

    def __str__(self):
        return self._text

    def __repr__(self):
        return f"Version({self._text!r})"

    def __eq__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return self._key == other._key

    def __lt__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return self._key < other._key

    def __hash__(self):
        return hash(self._key)


class Constraint:
    def __init__(self, name, specs=()):
        self.name = name
        self.specs = tuple(specs)  # (op, Version) pairs, all of which must hold

    @classmethod
    def parse(cls, requirement):
        match = _REQ_RE.fullmatch(requirement)
        if not match:
            raise ValueError(f"invalid requirement: {requirement!r}")
        name, rest = match.group(1), match.group(2).strip()
        specs = []
        if rest:
            for piece in rest.split(","):
                spec = _SPEC_RE.fullmatch(piece.strip())
                if not spec:
                    raise ValueError(f"invalid constraint {piece.strip()!r} in {requirement!r}")
                specs.append((spec.group(1), Version(spec.group(2))))
        return cls(name, specs)

    def allows(self, version):
        if not isinstance(version, Version):
            version = Version(version)
        return _satisfies(version, self.specs)

    def __eq__(self, other):
        if not isinstance(other, Constraint):
            return NotImplemented
        return self.name == other.name and self.specs == other.specs

    def __hash__(self):
        return hash((self.name, self.specs))

    def __repr__(self):
        return f"Constraint({self.name!r}, {list(self.specs)!r})"


def _satisfies(version, specs):
    return all(_OPS[op](version, bound) for op, bound in specs)


class _Search:
    """Feasibility oracle: finds any solution that honours the fixed choices.

    `packages` maps name -> list of (Version, [Constraint]) sorted newest first, so a
    candidate is identified by its position in that list.

    `fixed` maps name -> frozenset of allowed positions. A non-empty set means the
    package must be present, reachable from the roots, with one of those versions. An
    empty set means it must be absent.
    """

    def __init__(self, packages):
        self.packages = packages
        self.failures = []  # names blamed for dead ends, in the order they were hit

    def solve(self, root_specs, fixed):
        must = {}
        for name, specs in root_specs:
            must[name] = must.get(name, []) + list(specs)
        return self._dfs(must, {}, fixed)

    def _dfs(self, must, chosen, fixed):
        dom = {}
        for name, specs in must.items():
            entries = self.packages.get(name, [])
            if name in chosen:
                candidates = [chosen[name]] if _satisfies(entries[chosen[name]][0], specs) else []
            else:
                allowed = fixed.get(name)
                candidates = [
                    i
                    for i, (version, _) in enumerate(entries)
                    if (allowed is None or i in allowed) and _satisfies(version, specs)
                ]
            if not candidates:
                self.failures.append(name)
                return None
            dom[name] = candidates

        blamed = self._propagate(dom, chosen, fixed)
        if blamed is not None:
            self.failures.append(blamed)
            return None

        pending = sorted(name for name in dom if name not in chosen)
        if not pending:
            return dict(chosen)

        name = pending[0]
        entries = self.packages[name]
        for i in dom[name]:
            new_must = dict(must)
            for dep in entries[i][1]:
                new_must[dep.name] = new_must.get(dep.name, []) + list(dep.specs)
            result = self._dfs(new_must, {**chosen, name: i}, fixed)
            if result is not None:
                return result
        return None

    def _propagate(self, dom, chosen, fixed):
        """Drop candidates whose dependencies have no surviving candidate.

        Returns the name to blame if some domain becomes empty, otherwise None.
        """
        changed = True
        while changed:
            changed = False
            support = {}  # (name, specs) -> bool, valid until a domain changes
            for name in list(dom):
                if name in chosen:
                    continue
                kept = []
                blamed = None
                for i in dom[name]:
                    missing = next(
                        (dep for dep in self.packages[name][i][1]
                         if not self._supported(dep, dom, fixed, support)),
                        None,
                    )
                    if missing is None:
                        kept.append(i)
                    else:
                        blamed = missing.name
                if len(kept) == len(dom[name]):
                    continue
                if not kept:
                    return blamed
                dom[name] = kept
                changed = True
        return self._unreachable(dom, fixed)

    def _unreachable(self, dom, fixed):
        """A package fixed as present must be pullable from the roots by some candidate."""
        required = [name for name, allowed in fixed.items() if allowed and name not in dom]
        if not required:
            return None
        # Every package that some surviving candidate could still pull in, transitively.
        possible = set()
        stack = list(dom)
        while stack:
            owner = stack.pop()
            positions = dom[owner] if owner in dom else range(len(self.packages.get(owner, [])))
            for i in positions:
                for dep in self.packages[owner][i][1]:
                    if dep.name not in possible:
                        possible.add(dep.name)
                        if dep.name in self.packages:
                            stack.append(dep.name)
        for name in required:
            if name not in possible:
                return name
        return None

    def _supported(self, dep, dom, fixed, support):
        key = (dep.name, dep.specs)
        if key not in support:
            entries = self.packages.get(dep.name, [])
            if dep.name in dom:
                positions = dom[dep.name]
            else:
                allowed = fixed.get(dep.name)
                positions = [i for i in range(len(entries)) if allowed is None or i in allowed]
            support[key] = any(_satisfies(entries[i][0], dep.specs) for i in positions)
        return support[key]


def _reachable(root_names, packages):
    seen = set()
    stack = [name for name in root_names if name in packages]
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        for _, reqs in packages[name]:
            for dep in reqs:
                if dep.name in packages and dep.name not in seen:
                    stack.append(dep.name)
    return seen


def resolve(roots, index):
    packages = {}
    for name, versions in index.items():
        entries = [
            (Version(text), [Constraint.parse(req) for req in reqs])
            for text, reqs in versions.items()
        ]
        entries.sort(key=lambda entry: entry[0], reverse=True)
        packages[name] = entries

    root_specs = []
    for req in roots:
        dep = Constraint.parse(req)
        root_specs.append((dep.name, dep.specs))

    search = _Search(packages)
    if search.solve(root_specs, {}) is None:
        blamed = search.failures[0] if search.failures else roots[0]
        raise ResolutionError(f"no solution: constraints on package {blamed!r} cannot be satisfied")

    # Fix packages one at a time in name order. Each gets the highest version that still
    # admits a complete solution. Absent is the lowest choice, so it is only used when no
    # version of that package is possible. This gives the lexicographically greatest
    # assignment as defined in the spec.
    fixed = {}
    for name in sorted(_reachable([name for name, _ in root_specs], packages)):
        entries = packages[name]
        everything = frozenset(range(len(entries)))
        witness = search.solve(root_specs, {**fixed, name: everything})
        if witness is None:
            fixed[name] = frozenset()
            continue
        best = witness[name]
        while True:
            higher = frozenset(j for j in range(len(entries)) if entries[j][0] > entries[best][0])
            if not higher:
                break
            witness = search.solve(root_specs, {**fixed, name: higher})
            if witness is None:
                break
            best = witness[name]
        fixed[name] = frozenset([best])

    solution = search.solve(root_specs, fixed)
    return {name: str(packages[name][i][0]) for name, i in sorted(solution.items())}
