# Resolver spec

Index: `dict[str, dict[str, list[str]]]`, mapping package name to a mapping of version
string to its list of requirement strings. Example:

```python
INDEX = {
  "app":  {"1.0": ["web>=2", "db"]},
  "web":  {"1.0": [], "2.0": ["json<3"], "2.1": ["json>=3"]},
  "json": {"2.0": [], "3.0": []},
  "db":   {"1.0": ["json<3"]},
}
```

Requirement string grammar: `name` optionally followed by a comma-separated list of
constraints, each `<op><version>` with op in `==`, `!=`, `<`, `<=`, `>`, `>=`.
Examples: `web`, `web>=2`, `json>=2,<3`, `db==1.0`.

Versions: dotted integers, compared numerically component-wise, missing components are
zero (`1.0 == 1`, `1.10 > 1.9`).

`resolve(roots: list[str], index) -> dict[str, str]` returns the chosen version for every
package in the transitive closure, such that:

- every root requirement and every requirement of every chosen version is satisfied by the
  chosen version of that package (one version per package);
- preference: among all valid solutions, pick the one that is lexicographically greatest
  when packages are ordered by name and compared by version (i.e. the first package in
  alphabetical order gets the highest version it can, then the next, and so on);
- packages not reachable from the roots are not in the result;
- cycles in dependencies are fine (`a -> b -> a`);
- if no solution exists raise `ResolutionError` whose message names the package whose
  constraints could not be satisfied (the leaf where the search dead-ended, for example
  `b` when `a` requires `b<1` and only `b 1` and `b 2` exist), not only the root.

Correctness over speed, but the hidden tests include an index with a few hundred
versions where naive full enumeration will time out (60 s). Backtracking with
constraint propagation is enough.

Also export `Version` (comparable, hashable, `str()` gives the original string) and
`Constraint.parse("json>=2,<3")` with `.name` and `.allows(Version)`.
