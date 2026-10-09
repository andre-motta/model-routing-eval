import operator
import re
from functools import total_ordering


class ResolutionError(Exception):
    pass


_OPS = {
    "==": operator.eq,
    "!=": operator.ne,
    "<=": operator.le,
    ">=": operator.ge,
    "<": operator.lt,
    ">": operator.gt,
}
_NAME_RE = re.compile(r"\s*([^<>=!,\s]+)\s*(.*)$")
_CLAUSE_RE = re.compile(r"(==|!=|<=|>=|<|>)\s*(\S+)$")
_VERSION_RE = re.compile(r"\d+(\.\d+)*$")


@total_ordering
class Version:
    def __init__(self, s):
        text = str(s).strip()
        if not _VERSION_RE.match(text):
            raise ValueError(f"invalid version: {s!r}")
        self._text = text
        parts = [int(p) for p in text.split(".")]
        # Trailing zeros are insignificant ("1.0" == "1"), so strip them for comparison.
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
    def __init__(self, name, clauses=()):
        self.name = name
        self.clauses = tuple(clauses)  # (op, Version) pairs, all of which must hold

    @classmethod
    def parse(cls, requirement):
        match = _NAME_RE.match(requirement)
        if not match:
            raise ValueError(f"invalid requirement: {requirement!r}")
        name, rest = match.group(1), match.group(2).strip()
        clauses = []
        if rest:
            for part in rest.split(","):
                clause = _CLAUSE_RE.match(part.strip())
                if not clause:
                    raise ValueError(f"invalid constraint {part.strip()!r} in {requirement!r}")
                clauses.append((clause.group(1), Version(clause.group(2))))
        return cls(name, clauses)

    def allows(self, version):
        if not isinstance(version, Version):
            version = Version(version)
        return all(_OPS[op](version, bound) for op, bound in self.clauses)

    def __repr__(self):
        spec = ",".join(f"{op}{bound}" for op, bound in self.clauses)
        return f"Constraint({self.name}{spec})"


class _Search:
    def __init__(self, index):
        # name -> [(Version, [Constraint, ...])], highest version first
        self.releases = {}
        for name, versions in index.items():
            entries = [
                (Version(v), [Constraint.parse(r) for r in reqs])
                for v, reqs in versions.items()
            ]
            entries.sort(key=lambda entry: entry[0], reverse=True)
            self.releases[name] = entries
        self.dead_end = None

    def _fail(self, name):
        if self.dead_end is None:
            self.dead_end = name
        return None

    def _candidates(self, name, constraints):
        return [
            entry
            for entry in self.releases.get(name, ())
            if all(c.allows(entry[0]) for c in constraints)
        ]

    def solve(self, assigned, constraints):
        # Decide the alphabetically first required package that has no version yet, so
        # the highest-named-first preference is respected.
        pending = [name for name in constraints if name not in assigned]
        if not pending:
            return assigned
        name = min(pending)
        options = self._candidates(name, constraints[name])
        if not options:
            return self._fail(name)
        for version, requirements in options:
            result = self._try(name, version, requirements, assigned, constraints)
            if result is not None:
                return result
        return None

    def _try(self, name, version, requirements, assigned, constraints):
        assigned = {**assigned, name: version}
        constraints = {k: list(v) for k, v in constraints.items()}
        for req in requirements:
            if req.name in assigned:
                if not req.allows(assigned[req.name]):
                    return self._fail(req.name)
            else:
                constraints.setdefault(req.name, []).append(req)
        # Forward checking: every still-pending package must keep at least one candidate.
        for pending in constraints:
            if pending not in assigned and not self._candidates(pending, constraints[pending]):
                return self._fail(pending)
        return self.solve(assigned, constraints)


def resolve(roots, index):
    constraints = {}
    for root in roots:
        req = Constraint.parse(root)
        constraints.setdefault(req.name, []).append(req)

    search = _Search(index)
    solution = search.solve({}, constraints)
    if solution is None:
        raise ResolutionError(
            f"no solution: constraints on {search.dead_end!r} cannot be satisfied"
        )
    return {name: str(version) for name, version in solution.items()}
