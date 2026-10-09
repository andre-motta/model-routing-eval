from logstats.parse import parse_line, summarize


def test_parse_line():
    r = parse_line("2026-10-01T12:00:02Z GET /api/users/7 404 3.1")
    assert (r.method, r.status, r.latency_ms, r.bytes) == ("GET", 404, 3.1, 0)
    assert r.ts.utcoffset().total_seconds() == 0
    assert parse_line("garbage line here") is None


def test_summarize_sample():
    with open("sample.log") as f:
        s = summarize(f)
    assert s.malformed == 1
    assert s.total == 5
    assert s.by_status[500] == 1
    assert s.error_rate == 0.2
    assert s.bytes_total == 963
    assert s.p50_latency_ms == 12.5
    assert s.top_paths[0] == ("/api/users", 3)


def test_empty():
    s = summarize([])
    assert s.total == 0 and s.p95_latency_ms == 0.0 and s.error_rate == 0.0
