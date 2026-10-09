from datetime import datetime, timezone

from logstats.parse import Record, parse_line, summarize


def test_parse_full_line():
    assert parse_line("2026-10-01T12:00:00Z GET /api/users 200 12.5 843\n") == Record(
        datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc), "GET", "/api/users", 200, 12.5, 843
    )


def test_missing_bytes_is_zero():
    assert parse_line("2026-10-01T12:00:02Z GET /x 404 3.1").bytes == 0


def test_offset_converted_to_utc():
    rec = parse_line("2026-10-01T08:00:00-04:00 GET /x 200 1 1")
    assert rec.ts == datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)


def test_malformed():
    for bad in ["", "garbage line here", "2026-10-01T12:00:00Z GET /x 200",
                "2026-10-01T12:00:00Z GET /x 200 1.0 5 extra",
                "2026-10-01T12:00:00Z get /x 200 1.0",
                "2026-13-01T12:00:00Z GET /x 200 1.0",
                "2026-10-01T12:00:00 GET /x 200 1.0"]:
        assert parse_line(bad) is None, bad


def test_summarize_sample():
    with open("sample.log") as f:
        s = summarize(f)
    assert s.total == 5
    assert s.malformed == 1
    assert s.by_status == {200: 2, 201: 1, 404: 1, 500: 1}
    assert s.by_method == {"GET": 4, "POST": 1}
    assert s.p50_latency_ms == 12.5
    assert s.p95_latency_ms == 120.0
    assert s.bytes_total == 963
    assert s.error_rate == 0.2
    assert s.top_paths[0] == ("/api/users", 3)
    assert s.top_paths[1:] == [("/api/users/7", 1), ("/health", 1)]


def test_summarize_empty():
    s = summarize([])
    assert (s.total, s.p50_latency_ms, s.error_rate, s.top_paths) == (0, 0.0, 0.0, [])


def test_top_paths_limit_and_order():
    lines = [f"2026-10-01T12:00:00Z GET /p{i} 200 1" for i in "edcbaf"]
    assert [p for p, _ in summarize(lines).top_paths] == ["/pa", "/pb", "/pc", "/pd", "/pe"]
