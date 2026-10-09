from reporting import parse_rows, build_report


def test_small_report():
    rows = parse_rows(["e1,acme,api,1.5,100", "e2,acme,api,0.5,50", "e2,acme,api,0.5,50", "e3,beta,web,2,10"])
    rep = build_report(rows)
    assert rep[0] == {"tenant": "acme", "service": "api", "cpu_seconds": 2.0, "bytes_out": 150, "events": 2}
    assert rep[-1]["events"] == 3


def test_dedupe_scales_linearly():
    import time
    from reporting import dedupe_rows

    n = 50_000
    lines = [f"e{i},t{i % 10},s{i % 5},1.0,1" for i in range(n)]
    rows = parse_rows(lines + lines[:n // 2])
    start = time.perf_counter()
    out = dedupe_rows(rows)
    elapsed = time.perf_counter() - start
    assert [r.event_id for r in out] == [f"e{i}" for i in range(n)]
    # quadratic implementation takes tens of seconds here; linear takes milliseconds
    assert elapsed < 2.0
