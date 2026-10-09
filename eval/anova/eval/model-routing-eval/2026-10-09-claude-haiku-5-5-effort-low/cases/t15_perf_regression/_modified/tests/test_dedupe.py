import time

from reporting import UsageRow, dedupe_rows, parse_rows


def test_dedupe_keeps_first_occurrence_in_order():
    rows = parse_rows(["e1,acme,api,1,1", "e2,acme,api,1,1", "e1,acme,api,9,9", "e3,beta,web,1,1", "e2,acme,api,1,1"])
    assert [r.event_id for r in dedupe_rows(rows)] == ["e1", "e2", "e3"]
    assert dedupe_rows(rows)[0].cpu_seconds == 1.0


def test_dedupe_large_input_is_not_quadratic():
    # Quadratic dedupe (list membership) took ~5s on 30k rows; the set-based version takes milliseconds.
    rows = [UsageRow(f"evt-{i:08d}", "acme", "api", 1.0, 10) for i in range(30000)]
    rows += rows[:5000]

    start = time.perf_counter()
    out = dedupe_rows(rows)
    elapsed = time.perf_counter() - start

    assert len(out) == 30000
    assert [r.event_id for r in out] == [f"evt-{i:08d}" for i in range(30000)]
    assert elapsed < 1.0, f"dedupe_rows took {elapsed:.2f}s on 35k rows; likely regressed to O(n^2)"
