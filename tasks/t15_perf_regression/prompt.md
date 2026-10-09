Ops ticket: "The nightly usage report used to finish in under a minute. Since last
week's refactor it runs for over an hour on the same data (about 30k rows) and the ops
team kills it. Output looks correct when it does finish."

The `reporting` package is in this repo. Find the root cause, fix it without changing
the output or the public API, and add a regression test under `tests/` that would catch
it. Run the full test suite.
