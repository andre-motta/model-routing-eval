import functools
import re


class ResolutionError(Exception):
    pass


_OPS = ("==", "!=", "<=", ">=", "<", ">")
_CONSTRAINT_RE = re.compile(r"^(==|!=|<=|>=|<|>)\s*(\S+)$")
_NAME_RE = re.compile(r"^[A-Za-z0-9_.\-]+$")


@functools.total_ordering
class Version:
    def __init__(self, s):
        text = str(s).strip()
        parts = text.split(".")
        if not all(p.isdigit() for p in parts):
            raise ValueError(f"invalid version: {s!r}")
        self._text = text
        nums = [int(p) for p in parts]
        # Trailing zeros are insignificant: "1.0" == "1" and hash the same.
        while len(nums) > 1 and nums[-1] == 0:
            nums.pop()
        self._key = tuple(nums)

    def _cmp(self, other):
        a, b = self._key, other._key
        n = max(len(a), len(b))
        a = a + (0,) * (n - len(a))
        b = b + (0,) * (n - len(b))
        return (a > b) - (a < b)

    def __eq__(self, other):
        return isinstance(other, Version) and self._key == other._key

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


_OP_FUNCS = {
    "==": lambda v, t: v == t,
    "!=": lambda v, t: v != t,
    "<": lambda v, t: v < t,
    "<=": lambda v, t: v <= t,
    ">": lambda v, t: v > t,
    ">=": lambda v, t: v >= t,
}


class Constraint:
    def __init__(self, name, clauses):
        self.name = name
        self.clauses = tuple(clauses)  # tuple of (op, Version)

    @classmethod
    def parse(cls, requirement):
        text = requirement.strip()
        m = re.search(r"[=<>!]", text)
        name = text if m is None else text[: m.start()]
        name = name.strip()
        if not _NAME_RE.match(name):
            raise ValueError(f"invalid requirement: {requirement!r}")
        rest = "" if m is None else text[m.start():]
        clauses = []
        if rest:
            for piece in rest.split(","):
                cm = _CONSTRAINT_RE.match(piece.strip())
                if cm is None:
                    raise ValueError(f"invalid requirement: {requirement!r}")
                clauses.append((cm.group(1), Version(cm.group(2))))
        return cls(name, clauses)

    def allows(self, version):
        if not isinstance(version, Version):
            version = Version(version)
        return all(_OP_FUNCS[op](version, bound) for op, bound in self.clauses)

    def __repr__(self):
        spec = ",".join(f"{op}{v}" for op, v in self.clauses)
        return f"Constraint({self.name + spec!r})"


def _allows_all(constraints, version):
    return all(c.allows(version) for c in constraints)


def resolve(roots, index):
    # Parsed index: name -> [(Version, [Constraint]), ...] sorted highest first.
    parsed = {}
    for name, versions in index.items():
        entries = []
        for vs, reqs in versions.items():
            entries.append((Version(vs), [Constraint.parse(r) for r in reqs]))
        entries.sort(key=lambda e: e[0], reverse=True)
        parsed[name] = entries

    failure = {"name": None, "depth": -1}

    def fail(name, depth):
        if depth > failure["depth"]:
            failure["name"] = name
            failure["depth"] = depth

    def has_candidate(name, constraints):
        if name not in parsed:
            return False
        return any(_allows_all(constraints, v) for v, _ in parsed[name])

    def search(assign, reqs, depth):
        pending = [n for n in reqs if n not in assign]
        if not pending:
            return assign
        # Smallest pending name first, so the alphabetically first package
        # gets the highest version that still admits a full solution.
        name = min(pending)
        if name not in parsed:
            fail(name, depth)
            return None
        constraints = reqs[name]
        for version, deps in parsed[name]:
            if not _allows_all(constraints, version):
                continue
            new_reqs = dict(reqs)
            ok = True
            touched = set()
            for dep in deps:
                new_reqs[dep.name] = new_reqs.get(dep.name, []) + [dep]
                touched.add(dep.name)
            for dep_name in touched:
                cons = new_reqs[dep_name]
                if dep_name in assign:
                    if not _allows_all(cons, assign[dep_name]):
                        fail(dep_name, depth)
                        ok = False
                        break
                elif not has_candidate(dep_name, cons):
                    fail(dep_name, depth)
                    ok = False
                    break
            if not ok:
                continue
            new_assign = dict(assign)
            new_assign[name] = version
            result = search(new_assign, new_reqs, depth + 1)
            if result is not None:
                return result
        fail(name, depth)
        return None

    root_reqs = {}
    for root in roots:
        c = Constraint.parse(root)
        root_reqs.setdefault(c.name, []).append(c)
    for name in root_reqs:
        if not has_candidate(name, root_reqs[name]):
            raise ResolutionError(
                f"cannot satisfy constraints for package {name!r}"
            )

    solution = search({}, root_reqs, 0)
    if solution is None:
        culprit = failure["name"] or (roots[0] if roots else "")
        raise ResolutionError(
            f"cannot satisfy constraints for package {culprit!r}"
        )
    return {name: str(version) for name, version in solution.items()}
