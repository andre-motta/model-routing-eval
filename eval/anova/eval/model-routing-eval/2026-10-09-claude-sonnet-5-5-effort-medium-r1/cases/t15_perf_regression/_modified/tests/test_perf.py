import time

from reporting import UsageRow, build_report, dedupe_rows


def _rows(n, dup_every=3):
    return [UsageRow(f"e{i - i % dup_every}", "t", "s", 1.0, 1) for i in range(n)]


def test_dedupe_keeps_first_occurrence_order():
    rows = [UsageRow(e, "t", "s", 1.0, 1) for e in ["b", "a", "b", "c", "a"]]
    assert [r.event_id for r in dedupe_rows(rows)] == ["b", "a", "c"]


def test_dedupe_scales_linearly():
    # 60k rows with ~20k unique ids; quadratic behaviour takes many seconds, linear is milliseconds.
    rows = _rows(60_000)
    start = time.perf_counter()
    out = dedupe_rows(rows)
    elapsed = time.perf_counter() - start
    assert len(out) == 20_000
    assert elapsed < 1.0


def test_build_report_large_input_is_fast():
    rows = [UsageRow(f"e{i}", f"t{i % 10}", "s", 0.5, 1) for i in range(40_000)]
    start = time.perf_counter()
    rep = build_report(rows)
    assert time.perf_counter() - start < 2.0
    assert rep[-1]["events"] == 40_000
