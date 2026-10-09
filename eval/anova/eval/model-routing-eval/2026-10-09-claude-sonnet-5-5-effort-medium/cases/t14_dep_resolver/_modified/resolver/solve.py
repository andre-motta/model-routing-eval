import operator
import re
import sys


class ResolutionError(Exception):
    pass


class Version:
    def __init__(self, s):
        self._s = str(s)
        parts = self._s.strip().split(".")
        try:
            nums = [int(p) for p in parts]
        except ValueError:
            raise ValueError(f"invalid version: {s!r}")
        while nums and nums[-1] == 0:
            nums.pop()
        self._key = tuple(nums)

    def __str__(self):
        return self._s

    def __repr__(self):
        return f"Version({self._s!r})"

    def __hash__(self):
        return hash(self._key)

    def _cmp(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return (self._key > other._key) - (self._key < other._key)

    def __eq__(self, other):
        c = self._cmp(other)
        return c if c is NotImplemented else c == 0

    def __lt__(self, other):
        c = self._cmp(other)
        return c if c is NotImplemented else c < 0

    def __le__(self, other):
        c = self._cmp(other)
        return c if c is NotImplemented else c <= 0

    def __gt__(self, other):
        c = self._cmp(other)
        return c if c is NotImplemented else c > 0

    def __ge__(self, other):
        c = self._cmp(other)
        return c if c is NotImplemented else c >= 0


_OPS = {
    "==": operator.eq,
    "!=": operator.ne,
    "<=": operator.le,
    ">=": operator.ge,
    "<": operator.lt,
    ">": operator.gt,
}
_NAME_RE = re.compile(r"^\s*([^\s<>=!,]+)\s*(.*)$")
_CLAUSE_RE = re.compile(r"^\s*(==|!=|<=|>=|<|>)\s*(\S+)\s*$")


class Constraint:
    def __init__(self, name, clauses):
        self.name = name
        self.clauses = clauses  # list of (op string, Version)

    @classmethod
    def parse(cls, requirement):
        m = _NAME_RE.match(requirement)
        if not m:
            raise ValueError(f"invalid requirement: {requirement!r}")
        name, rest = m.groups()
        clauses = []
        if rest.strip():
            for part in rest.split(","):
                cm = _CLAUSE_RE.match(part)
                if not cm:
                    raise ValueError(f"invalid constraint {part!r} in {requirement!r}")
                clauses.append((cm.group(1), Version(cm.group(2))))
        return cls(name, clauses)

    def allows(self, version):
        if not isinstance(version, Version):
            version = Version(version)
        return all(_OPS[op](version, v) for op, v in self.clauses)

    def __repr__(self):
        return f"Constraint({self.name!r}, {[(o, str(v)) for o, v in self.clauses]})"


def prune(versions_of, root_names, failed):
    """Drop versions that can never be part of a solution: a requirement of theirs
    has no surviving version. Greatest fixpoint, so cycles are fine."""
    seen, stack = set(), list(root_names)
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        for _, _, reqs in versions_of(n):
            stack.extend(r.name for r in reqs)
    changed = True
    while changed:
        changed = False
        for n in seen:
            entries = versions_of(n)
            keep = []
            for e in entries:
                dead = next(
                    (r for r in e[2] if not any(r.allows(x[0]) for x in versions_of(r.name))),
                    None,
                )
                if dead is None:
                    keep.append(e)
                elif not failed:
                    failed.append(dead.name)
            if len(keep) != len(entries):
                entries[:] = keep
                changed = True


def resolve(roots, index):
    # Parse index lazily and cache: name -> [(Version, [Constraint])] highest first.
    parsed = {}

    def versions_of(name):
        if name not in parsed:
            entries = []
            for vs, reqs in index.get(name, {}).items():
                entries.append((Version(vs), vs, [Constraint.parse(r) for r in reqs]))
            entries.sort(key=lambda e: e[0], reverse=True)
            parsed[name] = entries
        return parsed[name]

    failed = []  # first dead-end package

    prune(versions_of, [Constraint.parse(r).name for r in roots], failed)

    def candidates(name, cons):
        return [e for e in versions_of(name) if all(c.allows(e[0]) for c in cons)]

    def add(cons, new):
        out = dict(cons)
        for c in new:
            out[c.name] = out.get(c.name, ()) + (c,)
        return out

    def fail(name):
        if not failed:
            failed.append(name)
        return None

    def search(chosen, cons):
        pending = [n for n in cons if n not in chosen]
        if not pending:
            return chosen
        name = min(pending)
        for ver, vstr, reqs in candidates(name, cons[name]):
            new_cons = add(cons, reqs)
            new_chosen = dict(chosen)
            new_chosen[name] = (ver, vstr)
            ok = True
            # forward check
            for r in reqs:
                if r.name in new_chosen:
                    if not r.allows(new_chosen[r.name][0]):
                        fail(r.name)
                        ok = False
                        break
                elif not candidates(r.name, new_cons[r.name]):
                    fail(r.name)
                    ok = False
                    break
            if not ok:
                continue
            res = search(new_chosen, new_cons)
            if res is not None:
                return res
        return fail(name)

    root_cons = [Constraint.parse(r) for r in roots]
    cons = add({}, root_cons)
    for r in root_cons:
        if not candidates(r.name, cons[r.name]):
            raise ResolutionError(
                f"no version of {failed[0] if failed else r.name} satisfies its constraints"
            )

    old = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old, 20000))
    try:
        res = search({}, cons)
    finally:
        sys.setrecursionlimit(old)
    if res is None:
        raise ResolutionError(
            f"cannot satisfy constraints for package {failed[0] if failed else '?'}"
        )
    return {n: v[1] for n, v in res.items()}
