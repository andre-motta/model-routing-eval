import functools
import re


class ResolutionError(Exception):
    pass


_VERSION_RE = re.compile(r"^\d+(\.\d+)*$")
_NAME_RE = re.compile(r"^\s*([A-Za-z0-9_.\-]+)\s*(.*)$")
_OP_RE = re.compile(r"^(==|!=|<=|>=|<|>)\s*(\S+)$")


@functools.total_ordering
class Version:
    def __init__(self, s):
        text = str(s).strip()
        if not _VERSION_RE.match(text):
            raise ValueError(f"invalid version: {s!r}")
        self._text = text
        parts = [int(p) for p in text.split(".")]
        # Trailing zeros are insignificant ("1.0" == "1"), so strip them for equality and hashing.
        while len(parts) > 1 and parts[-1] == 0:
            parts.pop()
        self._key = tuple(parts)

    def _cmp(self, other):
        a, b = self._key, other._key
        n = max(len(a), len(b))
        a = a + (0,) * (n - len(a))
        b = b + (0,) * (n - len(b))
        return (a > b) - (a < b)

    def __eq__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return self._key == other._key

    def __lt__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return self._cmp(other) < 0

    def __hash__(self):
        return hash(self._key)

    def __str__(self):
        return self._text

    def __repr__(self):
        return f"Version({self._text!r})"


class Constraint:
    def __init__(self, name, clauses=()):
        self.name = name
        self.clauses = tuple(clauses)  # (op, Version) pairs

    @classmethod
    def parse(cls, requirement):
        m = _NAME_RE.match(requirement)
        if not m or not m.group(1):
            raise ValueError(f"invalid requirement: {requirement!r}")
        name, rest = m.group(1), m.group(2).strip()
        clauses = []
        if rest:
            for piece in rest.split(","):
                om = _OP_RE.match(piece.strip())
                if not om:
                    raise ValueError(f"invalid constraint {piece.strip()!r} in {requirement!r}")
                clauses.append((om.group(1), Version(om.group(2))))
        return cls(name, clauses)

    def allows(self, version):
        if not isinstance(version, Version):
            version = Version(version)
        for op, bound in self.clauses:
            if op == "==":
                ok = version == bound
            elif op == "!=":
                ok = version != bound
            elif op == "<":
                ok = version < bound
            elif op == "<=":
                ok = version <= bound
            elif op == ">":
                ok = version > bound
            else:  # ">="
                ok = version >= bound
            if not ok:
                return False
        return True

    def __repr__(self):
        ops = ",".join(f"{op}{v}" for op, v in self.clauses)
        return f"Constraint({self.name!r}{', ' + ops if ops else ''})"


def resolve(roots, index):
    # Parse every version once, newest first, so candidate lists come out in preference order.
    versions = {
        name: sorted((Version(v) for v in vs), reverse=True)
        for name, vs in index.items()
    }
    requirements = {}  # (name, version_text) -> list of Constraint
    failure = []  # first package whose constraints could not be met

    def requirements_of(name, version):
        key = (name, str(version))
        if key not in requirements:
            requirements[key] = [Constraint.parse(r) for r in index[name][str(version)]]
        return requirements[key]

    def candidates(name, cons):
        return [
            v for v in versions.get(name, [])
            if all(c.allows(v) for c in cons)
        ]

    def search(assigned, cons):
        pending = [n for n in cons if n not in assigned]
        if not pending:
            return assigned
        name = min(pending)  # alphabetical order: lower names get preference first
        options = candidates(name, cons[name])
        if not options:
            if not failure:
                failure.append(name)
            return None
        for version in options:
            new_cons = {n: list(c) for n, c in cons.items()}
            ok = True
            for req in requirements_of(name, version):
                if req.name in assigned and not req.allows(assigned[req.name]):
                    ok = False
                    break
                new_cons.setdefault(req.name, []).append(req)
            if not ok:
                continue
            # Forward check: every still-unassigned package must keep at least one candidate.
            dead = next(
                (n for n in new_cons
                 if n not in assigned and n != name and not candidates(n, new_cons[n])),
                None,
            )
            if dead is not None:
                if not failure:
                    failure.append(dead)
                continue
            result = search({**assigned, name: version}, new_cons)
            if result is not None:
                return result
        return None

    root_cons = {}
    for r in roots:
        c = Constraint.parse(r)
        root_cons.setdefault(c.name, []).append(c)

    solution = search({}, root_cons)
    if solution is None:
        name = failure[0] if failure else (roots[0] if roots else "")
        raise ResolutionError(f"could not satisfy constraints on package {name!r}")
    return {n: str(v) for n, v in solution.items()}
