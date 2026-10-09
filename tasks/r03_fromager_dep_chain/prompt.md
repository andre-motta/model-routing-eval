This is the fromager repository (Python wheel builder). A virtualenv with the project
and test dependencies is already set up at `.venv`; run tests with
`.venv/bin/python -m pytest -o addopts="" tests/...`.

Issue #1214: fromager might "lie" about the reason of a dependency resolution failure

> Expected: fromager states the exact reason of the broken dependency chain.
> Actual: with ENABLE_REPEATABLE_BUILD_MODE and a broken indirect dependency, the error is
> logged under whatever top-level package is active in the logging context, e.g.
> `ERROR its-hub: Unable to resolve requirement specifier flashinfer-python==0.6.8.post1 ...`
> while the real chain is its-hub -> reward-hub -> vllm and vllm is the broken arc.
> fromager should say the resolution is broken because of vllm, not its-hub.

Fix it in the iterative bootstrapper (`src/fromager/bootstrapper/_bootstrapper.py`).
Design agreed in review:

- Add `Bootstrapper._dependency_chain_suffix(self, wi: WorkItem) -> str` returning
  `" (dependency chain: a==1 -> b==2 -> <wi.req>)"` built from `wi.why_snapshot`
  (each entry is `(_, req, version)`, rendered as `req.name==version`).
- Add `Bootstrapper._enrich_resolution_error(self, item: Phase, err: Exception) -> Exception`.
  For a `Resolve` phase item whose work item has a non-empty `why_snapshot`, return a
  new exception of the same shape with the chain suffix appended to the message:
  `resolvelib.resolvers.ResolverException` stays a `ResolverException`, `RuntimeError`
  stays a `RuntimeError`, anything else becomes `RuntimeError("<TypeName>: <msg><suffix>")`.
  For other phases or top-level requirements return `err` unchanged (same object).
- `_handle_phase_error()` must raise the enriched exception without a `from` clause,
  still inside the original handler, so the original is reachable via `__context__`
  but `__cause__` stays unset (the top-level formatter follows `__cause__` and would
  otherwise print the message twice). Enrichment must happen before the error is
  recorded in test mode or multiple-versions mode, and before the normal-mode raise.

Add tests to `tests/test_bootstrapper_iterative.py` and run that file.
