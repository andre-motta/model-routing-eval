import time

from reporting import UsageRow, dedupe_rows, build_report


def _rows(n, dup_every=3):
    return [UsageRow(f"e{i // dup_every}", "acme", "api", 1.0, 1) for i in range(n)]


def test_dedupe_keeps_first_occurrence_order():
    rows = [UsageRow(i, "t", "s", 1.0, 1) for i in ("b", "a", "b", "c", "a")]
    assert [r.event_id for r in dedupe_rows(rows)] == ["b", "a", "c"]


def test_dedupe_scales_linearly():
    # Quadratic dedupe takes tens of seconds at this size; linear takes milliseconds.
    rows = _rows(60000)
    start = time.perf_counter()
    out = dedupe_rows(rows)
    build_report(rows)
    elapsed = time.perf_counter() - start
    assert len(out) == 20000
    assert elapsed < 2.0
