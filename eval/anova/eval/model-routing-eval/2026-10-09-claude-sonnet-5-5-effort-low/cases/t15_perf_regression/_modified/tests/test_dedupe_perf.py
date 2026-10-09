import time

from reporting import UsageRow, dedupe_rows


def test_dedupe_preserves_first_occurrence_order():
    rows = [UsageRow(i, "t", "s", 1.0, 1) for i in ("b", "a", "b", "c", "a")]
    assert [r.event_id for r in dedupe_rows(rows)] == ["b", "a", "c"]


def test_dedupe_scales_linearly():
    # Quadratic dedupe takes tens of seconds at this size; linear takes milliseconds.
    rows = [UsageRow(f"e{i}", "t", "s", 1.0, 1) for i in range(200_000)]
    start = time.perf_counter()
    out = dedupe_rows(rows + rows[:1000])
    assert len(out) == 200_000
    assert time.perf_counter() - start < 2.0
