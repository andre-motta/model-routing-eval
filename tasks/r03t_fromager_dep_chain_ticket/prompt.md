This is the fromager repository (Python wheel builder). A virtualenv with the project
and test dependencies is already set up at `.venv`; run tests with
`.venv/bin/python -m pytest -o addopts="" tests/...`.

Fix the issue below. Add a regression test and run the relevant test file.

Issue #1214: fromager might "lie" about the reason of a dependency resolution failure

Expected: fromager states the exact reason of the broken dependency chain.
Actual: with ENABLE_REPEATABLE_BUILD_MODE and a broken indirect dependency, the error is
logged under whatever top-level package is active in the logging context, e.g.
`ERROR its-hub: Unable to resolve requirement specifier flashinfer-python==0.6.8.post1 ...`
while the real chain is its-hub -> reward-hub -> vllm and vllm is the broken arc.
fromager should say the resolution is broken because of vllm, not its-hub.
