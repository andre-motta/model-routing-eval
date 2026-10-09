import functools
import operator
import re


class ResolutionError(Exception):
    pass


@functools.total_ordering
class Version:
    def __init__(self, s):
        self._s = str(s)
        parts = self._s.strip().split(".")
        try:
            nums = [int(p) for p in parts]
        except ValueError:
            raise ValueError(f"invalid version: {s!r}") from None
        while len(nums) > 1 and nums[-1] == 0:
            nums.pop()
        self._key = tuple(nums)

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

    def __str__(self):
        return self._s

    def __repr__(self):
        return f"Version({self._s!r})"


_OPS = {
    "==": operator.eq,
    "!=": operator.ne,
    "<=": operator.le,
    ">=": operator.ge,
    "<": operator.lt,
    ">": operator.gt,
}
_CLAUSE = re.compile(r"^\s*(==|!=|<=|>=|<|>)\s*([0-9][0-9.]*)\s*$")


class Constraint:
    def __init__(self, name, clauses=()):
        self.name = name
        self.clauses = tuple(clauses)

    @classmethod
    def parse(cls, requirement):
        m = re.match(r"^\s*([^\s<>=!,]+)\s*(.*)$", requirement)
        if not m:
            raise ValueError(f"invalid requirement: {requirement!r}")
        name, rest = m.groups()
        clauses = []
        if rest.strip():
            for part in rest.split(","):
                cm = _CLAUSE.match(part)
                if not cm:
                    raise ValueError(f"invalid requirement: {requirement!r}")
                clauses.append((cm.group(1), Version(cm.group(2))))
        return cls(name, clauses)

    def allows(self, version):
        if not isinstance(version, Version):
            version = Version(version)
        return all(_OPS[op](version, v) for op, v in self.clauses)


def resolve(roots, index):
    parsed = {}

    def deps_of(name, ver):
        key = (name, ver)
        if key not in parsed:
            parsed[key] = [Constraint.parse(r) for r in index[name][ver]]
        return parsed[key]

    versions = {
        n: sorted(((Version(v), v) for v in vs), reverse=True) for n, vs in index.items()
    }
    failed = []

    def candidates(name, cons):
        return [raw for v, raw in versions.get(name, ()) if all(c.allows(v) for c in cons)]

    def search(assigned, cons):
        pending = sorted(n for n in cons if n not in assigned)
        if not pending:
            return assigned
        name = pending[0]
        for raw in candidates(name, cons[name]):
            new_cons = {n: list(cs) for n, cs in cons.items()}
            new_assigned = dict(assigned)
            new_assigned[name] = raw
            ok = True
            for c in deps_of(name, raw):
                new_cons.setdefault(c.name, []).append(c)
                if c.name in new_assigned:
                    if not c.allows(Version(new_assigned[c.name])):
                        failed.append(c.name)
                        ok = False
                        break
                elif not candidates(c.name, new_cons[c.name]):
                    failed.append(c.name)
                    ok = False
                    break
            if ok:
                res = search(new_assigned, new_cons)
                if res is not None:
                    return res
        if not failed or failed[-1] != name:
            failed.append(name)
        return None

    cons = {}
    for r in roots:
        c = Constraint.parse(r)
        cons.setdefault(c.name, []).append(c)
    for n, cs in cons.items():
        if not candidates(n, cs):
            raise ResolutionError(f"no version of {n} satisfies constraints")
    res = search({}, cons)
    if res is None:
        raise ResolutionError(
            f"cannot satisfy constraints for package {failed[0] if failed else '?'}"
        )
    return res
