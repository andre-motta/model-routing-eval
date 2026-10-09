This is the fromager repository (Python wheel builder). A virtualenv with the project
and test dependencies is already set up at `.venv`; run tests with
`.venv/bin/python -m pytest -o addopts="" tests/...`.

Issue #1146: get_metadata_for_wheel() may return wrong metadata

> `get_metadata_for_wheel` returns the first match for `name.endswith(".dist-info/METADATA")`.
> This is a bad assumption. A wheel can contain multiple `.dist-info` directories. It's
> common to include dist-info directories of vendored packages.
>
> `get_metadata_for_wheel` should only look at `dist-info` directories in the root of the
> wheel. Or better: parse the URL, split the name, and use
> `{dist_name}-{dist_version}.dist-info/METADATA`.

Fix it. Requirements agreed in review:

- Add a module `src/fromager/pkgmetadata/pep376.py` with two helpers, both exported from
  `fromager.pkgmetadata`:
  - `verbatim_dist_name(wheel_filename: str) -> str`: the distribution name exactly as
    spelled in the wheel filename (`MarkupSafe`, not `markupsafe`). Validate the filename
    with `packaging.utils.parse_wheel_filename` first so malformed names or non-wheel
    extensions raise `packaging.utils.InvalidWheelFilename`.
  - `dist_info_name(wheel_filename: str) -> str`: `{verbatim_name}-{version}.dist-info`,
    version taken verbatim from the filename, same validation.
- In `candidate.py` add `_wheel_metadata_path(url: str) -> str` that takes a wheel URL
  (last path segment is the filename; ignore query string and fragment) and returns
  `f"{dist_info_name(filename)}/METADATA"`. `get_metadata_for_wheel()` uses it to read
  exactly that member from the zip. If the member is missing raise `ValueError`.
- Reuse `verbatim_dist_name` wherever `wheels.py` or `dependencies.py` currently
  re-implements the "first segment of the filename" logic.

Keep existing tests passing; add tests for the helpers and the fallback path.
