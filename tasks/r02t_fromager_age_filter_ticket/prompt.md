This is the fromager repository (Python wheel builder). A virtualenv with the project
and test dependencies is already set up at `.venv`; run tests with
`.venv/bin/python -m pytest -o addopts="" tests/...`.

Fix the issue below. Add a regression test and run the relevant test file.

Bug: with `--max-release-age` in multi-version bootstrap mode, a package that is pinned in
the constraints file (for example `boto3==1.35.88`) to a version older than the age window
has every candidate removed by the age filter and resolution fails silently. In
single-version mode the fallback keeps all candidates anyway, but logs a misleading
"keeping all to avoid empty resolution" warning for a package the user explicitly pinned.
A constraint is explicit user intent and should not be overridden by the age heuristic.
