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
        return isinstance(other, Version) and self._key == other._key

    def __lt__(self, other):
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
_CON_RE = re.compile(r"^(==|!=|<=|>=|<|>)\s*(\S+)$")


class Constraint:
    def __init__(self, name, specs=()):
        self.name = name
        self.specs = tuple(specs)

    @classmethod
    def parse(cls, requirement):
        m = re.match(r"^\s*([^\s=!<>,]+)\s*(.*)$", requirement)
        if not m:
            raise ValueError(f"invalid requirement: {requirement!r}")
        name, rest = m.group(1), m.group(2).strip()
        specs = []
        if rest:
            for part in rest.split(","):
                cm = _CON_RE.match(part.strip())
                if not cm:
                    raise ValueError(f"invalid constraint: {part!r}")
                specs.append((cm.group(1), Version(cm.group(2))))
        return cls(name, specs)

    def allows(self, version):
        if not isinstance(version, Version):
            version = Version(version)
        return all(_OPS[op](version, v) for op, v in self.specs)


def resolve(roots, index):
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 20000))
    versions = {
        n: sorted(((Version(v), v) for v in vs), key=lambda t: t[0], reverse=True)
        for n, vs in index.items()
    }
    parsed = {}

    def reqs(name, vstr):
        key = (name, vstr)
        if key not in parsed:
            parsed[key] = [Constraint.parse(r) for r in index[name][vstr]]
        return parsed[key]

    failed = []

    def candidates(name, cons):
        return [
            (v, s) for v, s in versions.get(name, ())
            if all(c.allows(v) for c in cons)
        ]

    def fail(name):
        if not failed:
            failed.append(name)

    def search(chosen, cons):
        pending = sorted(n for n in cons if n not in chosen)
        if not pending:
            return chosen
        name = pending[0]
        for v, s in candidates(name, cons[name]):
            new_cons = {k: list(c) for k, c in cons.items()}
            ok = True
            for r in reqs(name, s):
                if r.name in chosen:
                    if not r.allows(chosen[r.name][0]):
                        fail(name)
                        ok = False
                        break
                    continue
                new_cons.setdefault(r.name, []).append(r)
                if not candidates(r.name, new_cons[r.name]):
                    fail(r.name)
                    ok = False
                    break
            if not ok:
                continue
            new_chosen = dict(chosen)
            new_chosen[name] = (v, s)
            res = search(new_chosen, new_cons)
            if res is not None:
                return res
        fail(name)
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
    return {n: s for n, (v, s) in res.items()}
