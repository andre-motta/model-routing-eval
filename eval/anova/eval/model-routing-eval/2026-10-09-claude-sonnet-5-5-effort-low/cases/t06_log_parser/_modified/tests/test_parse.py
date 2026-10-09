from logstats.parse import parse_line, summarize


def test_parse_line():
    r = parse_line("2026-10-01T12:00:02Z GET /api/users/7 404 3.1")
    assert (r.method, r.path, r.status, r.latency_ms, r.bytes) == ("GET", "/api/users/7", 404, 3.1, 0)
    assert r.ts.utcoffset().total_seconds() == 0
    assert parse_line("garbage line here") is None
    assert parse_line("") is None


def test_summarize_sample():
    with open("sample.log") as f:
        s = summarize(f)
    assert s.malformed == 1
    assert s.total == sum(s.by_status.values())
    assert s.top_paths[0] == ("/api/users", 3)
