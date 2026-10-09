from datetime import datetime, timezone

from logstats.parse import Record, parse_line, summarize


def test_parse_full_and_optional_bytes():
    r = parse_line("2026-10-01T12:00:00Z GET /api/users 200 12.5 843")
    assert r == Record(datetime(2026, 10, 1, 12, tzinfo=timezone.utc), "GET", "/api/users", 200, 12.5, 843)
    assert parse_line("2026-10-01T12:00:02Z GET /x 404 3.1").bytes == 0


def test_malformed():
    for bad in ["", "garbage line here", "2026-10-01T12:00:00Z GET /x abc 1.0",
                "nope GET /x 200 1.0", "2026-10-01T12:00:00Z GET /x 200 1.0 5 extra",
                "2026-10-01T12:00:00Z GET /x 200 nan"]:
        assert parse_line(bad) is None


def test_summarize_sample():
    with open("sample.log") as f:
        s = summarize(f)
    assert s.total == 5 and s.malformed == 1
    assert s.by_status == {200: 2, 201: 1, 404: 1, 500: 1}
    assert s.by_method == {"GET": 4, "POST": 1}
    assert s.p50_latency_ms == 12.5 and s.p95_latency_ms == 120.0
    assert s.bytes_total == 963
    assert s.error_rate == 0.2
    assert s.top_paths[0] == ("/api/users", 3)


def test_empty():
    s = summarize([])
    assert s.total == 0 and s.p50_latency_ms == 0.0 and s.error_rate == 0.0 and s.top_paths == []
