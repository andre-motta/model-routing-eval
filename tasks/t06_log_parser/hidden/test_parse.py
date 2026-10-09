from datetime import timezone

from logstats.parse import parse_line, summarize

LINES = [
    "2026-10-01T12:00:00Z GET /a 200 10 100",
    "2026-10-01T12:00:01Z GET /a 200 20 100",
    "2026-10-01T12:00:02Z POST /b 201 30",
    "2026-10-01T12:00:03Z GET /c 503 40 5",
    "nope",
    "2026-10-01T12:00:04Z GET /a 200 50 1",
    "2026-10-01T12:00:05Z DELETE /b 204 60.5 0",
    "2026-10-01T12:00:06Z GET /d 500 70 0",
    "2026-10-01T12:00:07Z GET /e 200 80 0",
    "2026-10-01T12:00:08Z GET /f 200 90 0",
    "2026-10-01T12:00:09Z GET /g 200 100 0",
]


def test_parse_line():
    r = parse_line("2026-10-01T12:00:02Z GET /api/users/7 404 3.1")
    assert r.ts.tzinfo is not None and r.ts.utcoffset().total_seconds() == 0
    assert (r.method, r.path, r.status, r.latency_ms, r.bytes) == ("GET", "/api/users/7", 404, 3.1, 0)
    assert parse_line("garbage") is None
    assert parse_line("2026-10-01T12:00:02Z GET /x abc 3.1") is None


def test_summary():
    s = summarize(LINES)
    assert s.total == 10 and s.malformed == 1
    assert s.by_status == {200: 6, 201: 1, 503: 1, 204: 1, 500: 1}
    assert s.by_method == {"GET": 8, "POST": 1, "DELETE": 1}
    assert s.bytes_total == 206
    assert abs(s.error_rate - 0.2) < 1e-9
    assert s.p50_latency_ms == 50 and s.p95_latency_ms == 100
    assert s.top_paths == [("/a", 3), ("/b", 2), ("/c", 1), ("/d", 1), ("/e", 1)]


def test_empty():
    s = summarize([])
    assert s.total == 0 and s.p50_latency_ms == 0.0 and s.error_rate == 0.0 and s.top_paths == []
