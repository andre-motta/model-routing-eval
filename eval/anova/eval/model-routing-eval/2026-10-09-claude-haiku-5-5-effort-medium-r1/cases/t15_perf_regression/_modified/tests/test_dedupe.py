from reporting import UsageRow, dedupe_rows


class CountingId(str):
    """str that counts equality comparisons, so tests can see how dedupe looks up ids."""

    eq_calls = 0

    def __eq__(self, other):
        CountingId.eq_calls += 1
        return str.__eq__(self, other)

    def __ne__(self, other):
        CountingId.eq_calls += 1
        return str.__ne__(self, other)

    __hash__ = str.__hash__


def test_dedupe_keeps_first_occurrence_in_order():
    rows = [
        UsageRow("e2", "acme", "api", 1.0, 1),
        UsageRow("e1", "acme", "api", 1.0, 1),
        UsageRow("e2", "acme", "api", 9.0, 9),
        UsageRow("e3", "beta", "web", 1.0, 1),
    ]
    out = dedupe_rows(rows)
    assert [r.event_id for r in out] == ["e2", "e1", "e3"]
    assert out[0].cpu_seconds == 1.0


def test_dedupe_lookup_does_not_scale_quadratically():
    # Each unique id must be checked against the seen set, not compared against every
    # earlier id. A list-based membership check makes about n*(n-1)/2 comparisons here.
    n = 3000
    rows = [UsageRow(CountingId(f"event-{i}"), "acme", "api", 0.5, 10) for i in range(n)]
    CountingId.eq_calls = 0
    out = dedupe_rows(rows)
    assert len(out) == n
    assert CountingId.eq_calls < n
