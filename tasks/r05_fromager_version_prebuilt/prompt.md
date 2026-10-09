This is the fromager repository (Python wheel builder). A virtualenv with the project
and test dependencies is already set up at `.venv`; run tests with
`.venv/bin/python -m pytest -o addopts="" tests/...`.

Package settings already support version-specific overrides of `pre_built` and
`wheel_server_url` under `variants.<variant>.versions.<version>` (see
`src/fromager/packagesettings/_pbi.py`, `is_pre_built()` and `get_wheel_server_url()`),
but the START phase of the iterative bootstrapper (`src/fromager/bootstrapper/_start.py`)
resolves the download URL before it knows the version, so a version that is pre-built
while the variant default is source (or the other way round, or a version with a
different wheel server) ends up with a URL of the wrong kind. Also, resolved versions can
carry a local segment (`2.8.0+cpu`) which does not match the YAML key `2.8.0`.

Make this work end to end:

1. `_pbi.py`:
   - `is_pre_built(version)` and `get_wheel_server_url(version)` strip the local version
     segment before the version-specific lookup (use `Version(version.public)`), like
     `get_changelog` and `get_patches` already do.
   - `is_pre_built(version)` consults the `is_pre_built` override hook only when a version
     is given (the version-specific path); with no version it returns the variant default
     without calling the hook. It calls the hook through
     `overrides.find_and_invoke(self.package, "is_pre_built", _default_is_pre_built,
     version=version, variant=self.variant)` where the module-level
     `_default_is_pre_built(*, version, variant)` returns `None` (defer to YAML). A
     non-None hook result wins over YAML.
   - The `pre_built` and `wheel_server_url` properties delegate to `is_pre_built()` and
     `get_wheel_server_url()` with no version, so there is a single code path.
   - `_models.py`: a bare `versions:` key in YAML (parsed as None) or an omitted key
     yields an empty mapping.
2. `wheels.get_wheel_server_urls(ctx, req, cache_wheel_server_url=..., version=None)`
   accepts an optional `version` and uses the version-specific wheel server URL when given.
3. `_start.py`: add a module-level function
   `_re_resolve_url(ctx, req, req_type, resolved_version, pre_built, cache_wheel_server_url) -> str | None`.
   For `pre_built=True` it builds the pinned requirement `name==version`, gets the wheel
   server URLs for that version and calls `wheels.resolve_prebuilt_wheel(ctx=, req=,
   wheel_server_urls=, req_type=)`, returning the URL as a string, or `None` if that
   raises `ExceptionGroup`. For `pre_built=False` it uses `sources.get_source_provider`
   with the package's sdist server and `resolver.find_all_matching_from_provider`,
   returning the first match's URL or `None`.
   In the START phase, after `wi.pbi_pre_built = pbi.is_pre_built(wi.resolved_version)`:
   re-resolve when `wi.pbi_pre_built != pbi.pre_built`, or when the package is pre-built
   and `pbi.get_wheel_server_url(wi.resolved_version) != pbi.wheel_server_url`. Log at
   INFO before, use the new URL on success, log a WARNING and keep the original URL on
   `None`. This must happen before the work item is added to the dependency graph (so the
   graph stores the final URL) and before the has-been-seen check (so a second parent of
   an already-seen package still gets its edge recorded).
4. Docs: bump the related `versionadded` directives in `_pbi.py` to 0.95.0 and mention the
   behaviour in `docs/concepts/package-settings.rst` and `docs/concepts/hooks-and-overrides.rst`.

Add tests in `tests/test_packagesettings.py` and `tests/test_bootstrapper_iterative.py`
and run both files.
