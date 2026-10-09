`metrics.Counter` loses increments when used from several threads, and `snapshot()`
sometimes returns a dict that is mid-update. `tests/test_metrics.py` reproduces it
(it is non-deterministic, run it a few times). Fix the root cause with proper
synchronisation, keep the API, keep `snapshot()` returning a plain dict copy, and do
not serialise unrelated counters behind one global lock if you can avoid it. Run the
tests.
