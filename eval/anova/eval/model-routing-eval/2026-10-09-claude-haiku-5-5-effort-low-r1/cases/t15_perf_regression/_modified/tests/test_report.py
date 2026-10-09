from reporting import UsageRow, parse_rows, build_report, dedupe_rows


def test_small_report():
    rows = parse_rows(["e1,acme,api,1.5,100", "e2,acme,api,0.5,50", "e2,acme,api,0.5,50", "e3,beta,web,2,10"])
    rep = build_report(rows)
    assert rep[0] == {"tenant": "acme", "service": "api", "cpu_seconds": 2.0, "bytes_out": 150, "events": 2}
    assert rep[-1]["events"] == 3


class CountingId(str):
    """str that counts equality checks, to observe how many comparisons dedupe does."""

    eq_calls = 0

    def __eq__(self, other):
        CountingId.eq_calls += 1
        return str.__eq__(self, other)

    __hash__ = str.__hash__


def test_dedupe_is_linear_not_quadratic():
    # A list-based membership check does ~n^2/2 comparisons here (about 4.5M for n=3000);
    # a set-based one does none on unique ids. Counting comparisons avoids timing flakiness.
    n = 3000
    rows = [UsageRow(CountingId(f"e{i}"), "acme", "api", 0.1, 1) for i in range(n)]
    CountingId.eq_calls = 0
    out = dedupe_rows(rows)
    assert len(out) == n
    assert CountingId.eq_calls <= n


def test_dedupe_keeps_first_occurrence_order():
    rows = [UsageRow(e, "acme", "api", 1.0, 1) for e in ["b", "a", "b", "c", "a"]]
    assert [r.event_id for r in dedupe_rows(rows)] == ["b", "a", "c"]
