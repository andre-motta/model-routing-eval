from reporting import UsageRow, build_report, dedupe_rows


class CountingId(str):
    """String event id that counts equality checks, to catch quadratic membership tests."""

    eq_calls = 0

    def __eq__(self, other):
        CountingId.eq_calls += 1
        return str.__eq__(self, other)

    __hash__ = str.__hash__


def test_dedupe_is_linear_in_rows():
    # A list-based "seen" check does ~n^2/2 comparisons (about 30k rows took over an hour in prod).
    # A set-based check does ~0 comparisons for distinct ids, so this bound is far below the quadratic cost.
    n = 2000
    rows = [UsageRow(CountingId(f"e{i}"), "acme", "api", 0.1, 10) for i in range(n)]
    CountingId.eq_calls = 0
    out = dedupe_rows(rows)
    assert len(out) == n
    assert CountingId.eq_calls <= n


def test_dedupe_keeps_first_occurrence_order():
    rows = [
        UsageRow("e2", "acme", "api", 1.0, 1),
        UsageRow("e1", "acme", "api", 1.0, 1),
        UsageRow("e2", "acme", "api", 9.0, 9),
        UsageRow("e3", "beta", "web", 1.0, 1),
        UsageRow("e1", "acme", "api", 9.0, 9),
    ]
    out = dedupe_rows(rows)
    assert [r.event_id for r in out] == ["e2", "e1", "e3"]
    assert out[0].cpu_seconds == 1.0


def test_build_report_large_input_with_retries():
    rows = [UsageRow(f"e{i}", f"t{i % 5}", f"s{i % 3}", 0.5, 10) for i in range(30000)]
    rows += rows[:3000]  # collector retries re-send the same event ids
    rep = build_report(rows)
    assert rep[-1] == {"tenant": "*", "service": "*", "cpu_seconds": 15000.0, "bytes_out": 300000, "events": 30000}
