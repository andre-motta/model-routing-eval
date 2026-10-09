This is the fromager repository (Python wheel builder). A virtualenv with the project
and test dependencies is already set up at `.venv`; run tests with
`.venv/bin/python -m pytest -o addopts="" tests/...`.

Implement the following change to the resolver's max-release-age handling
(`src/fromager/resolver.py`, `find_all_matching_from_provider()`, and its callers in
`src/fromager/bootstrap_requirement_resolver.py`).

1. Replace the boolean `fallback_on_empty_age_filter` parameter of
   `find_all_matching_from_provider()` with an `AgeFallback` enum (exported from
   `fromager.resolver`) selecting what happens when age filtering removes every candidate:
   - `AgeFallback.ALL`: keep every candidate (this is the single-version default and the
     current behaviour, including its "keeping all to avoid empty resolution" warning)
   - `AgeFallback.NEWEST`: keep only the single newest candidate (new)
   - `AgeFallback.NONE`: return an empty list
   Name the new keyword parameter `age_fallback`, default `AgeFallback.ALL`.
   Multi-version bootstrap mode must use `AgeFallback.NEWEST`, so that when a dependency
   has no release inside the age window (bar from two years ago depended on by a recent
   foo) its newest version is built instead of failing, which avoids cascading failures
   in the dependent package.

2. Packages that have an explicit constraint (the provider's `constraints` object returns
   a constraint for the requirement name) skip age filtering entirely. A constraint is
   explicit user intent and must not be overridden by the age heuristic. Log at INFO on the
   `fromager.resolver` logger: `"<name>: skipping age filter for constrained package (<N> candidate(s))"`.
   Previously, in multi-version mode a constrained package pinned to a version older than
   the window lost every candidate and resolution failed silently; in single-version mode
   the fallback kept all candidates but logged the misleading warning.

Update docstrings, add tests in `tests/test_cooldown.py` and
`tests/test_bootstrap_requirement_resolver.py`, and run both files.
