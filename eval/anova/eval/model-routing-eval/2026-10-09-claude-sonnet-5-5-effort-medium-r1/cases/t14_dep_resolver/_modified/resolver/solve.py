import functools
import operator
import re
import sys


class ResolutionError(Exception):
    pass


@functools.total_ordering
class Version:
    def __init__(self, s):
        self._s = str(s).strip()
        try:
            parts = [int(p) for p in self._s.split(".")]
        except ValueError:
            raise ValueError(f"invalid version: {s!r}")
        while len(parts) > 1 and parts[-1] == 0:
            parts.pop()
        self._key = tuple(parts)

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
_CLAUSE = re.compile(r"^(==|!=|<=|>=|<|>)\s*(\S+)$")


class Constraint:
    def __init__(self, name, clauses=()):
        self.name = name
        self.clauses = tuple(clauses)  # (op string, Version)

    @classmethod
    def parse(cls, requirement):
        m = re.match(r"^\s*([^=!<>\s,]+)\s*(.*?)\s*$", requirement)
        if not m:
            raise ValueError(f"invalid requirement: {requirement!r}")
        name, rest = m.groups()
        clauses = []
        if rest:
            for part in rest.split(","):
                cm = _CLAUSE.match(part.strip())
                if not cm:
                    raise ValueError(f"invalid constraint {part!r} in {requirement!r}")
                clauses.append((cm.group(1), Version(cm.group(2))))
        return cls(name, clauses)

    def allows(self, version):
        if not isinstance(version, Version):
            version = Version(version)
        return all(_OPS[op](version, v) for op, v in self.clauses)


def resolve(roots, index):
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 10000))
    versions = {
        name: sorted((Version(v) for v in vs), reverse=True)
        for name, vs in index.items()
    }
    reqs_cache = {}

    def reqs_of(name, v):
        key = (name, v)
        if key not in reqs_cache:
            reqs_cache[key] = [Constraint.parse(r) for r in index[name][str(v)]]
        return reqs_cache[key]

    fail = {"depth": -1, "name": None}

    def note(name, depth):
        if depth > fail["depth"]:
            fail["depth"], fail["name"] = depth, name

    def candidates(name, cons):
        return [v for v in versions.get(name, ()) if all(c.allows(v) for c in cons)]

    def search(chosen, cons, depth):
        pending = [n for n in cons if n not in chosen]
        if not pending:
            return chosen
        name = min(pending)
        for v in candidates(name, cons[name]):
            new_cons = dict(cons)
            ok = True
            for r in reqs_of(name, v):
                if r.name == name:
                    if not r.allows(v):
                        ok = False
                        break
                    continue
                merged = new_cons.get(r.name, ()) + (r,)
                new_cons[r.name] = merged
                if r.name in chosen:
                    if not r.allows(chosen[r.name]):
                        note(r.name, depth + 1)
                        ok = False
                        break
                elif not candidates(r.name, merged):
                    note(r.name, depth + 1)
                    ok = False
                    break
            if not ok:
                continue
            chosen[name] = v
            res = search(chosen, new_cons, depth + 1)
            if res is not None:
                return res
            del chosen[name]
        note(name, depth)
        return None

    cons = {}
    for r in roots:
        c = Constraint.parse(r)
        cons[c.name] = cons.get(c.name, ()) + (c,)
    for name, cs in cons.items():
        if not candidates(name, cs):
            raise ResolutionError(f"no version of {name} satisfies the requirements")

    result = search({}, cons, 0)
    if result is None:
        raise ResolutionError(
            f"could not satisfy constraints for package {fail['name']}"
        )
    return {n: str(v) for n, v in sorted(result.items())}
