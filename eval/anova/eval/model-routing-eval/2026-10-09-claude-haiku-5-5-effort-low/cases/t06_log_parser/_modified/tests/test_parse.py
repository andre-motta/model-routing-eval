from datetime import datetime, timezone
from pathlib import Path

from logstats.parse import parse_line, summarize

SAMPLE = Path(__file__).resolve().parent.parent / "sample.log"


def test_parse_line_full():
    rec = parse_line("2026-10-01T12:00:00Z GET /api/users 200 12.5 843")
    assert rec is not None
    assert rec.ts == datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert (rec.method, rec.path, rec.status, rec.latency_ms, rec.bytes) == (
        "GET", "/api/users", 200, 12.5, 843)


def test_parse_line_missing_bytes_is_zero():
    rec = parse_line("2026-10-01T12:00:02Z GET /api/users/7 404 3.1")
    assert rec is not None and rec.bytes == 0 and rec.status == 404


def test_parse_line_converts_offset_to_utc():
    rec = parse_line("2026-10-01T14:00:00+02:00 GET / 200 1")
    assert rec is not None
    assert rec.ts.utcoffset().total_seconds() == 0
    assert rec.ts.hour == 12


def test_parse_line_malformed():
    bad = [
        "garbage line here",
        "",
        "2026-10-01T12:00:00Z GET /x abc 1.0",
        "2026-10-01T12:00:00Z get /x 200 1.0",
        "2026-10-01T12:00:00Z GET /x 200 nan",
        "2026-10-01T12:00:00Z GET /x 200 -1",
        "2026-10-01T12:00:00 GET /x 200 1.0",
        "2026-13-01T12:00:00Z GET /x 200 1.0",
        "2026-10-01T12:00:00Z GET /x 200 1.0 1 2",
    ]
    for line in bad:
        assert parse_line(line) is None, line


def test_summarize_sample():
    with SAMPLE.open() as fh:
        s = summarize(fh)
    assert s.total == 5
    assert s.malformed == 1
    assert s.by_status == {200: 2, 201: 1, 404: 1, 500: 1}
    assert s.by_method == {"GET": 4, "POST": 1}
    assert s.bytes_total == 843 + 120 + 0 + 0 + 0
    assert s.error_rate == 1 / 5
    assert s.top_paths == [("/api/users", 3), ("/api/users/7", 1), ("/health", 1)]
    # sorted latencies: 0.4, 3.1, 12.5, 40, 120.0
    assert s.p50_latency_ms == 12.5
    assert s.p95_latency_ms == 120.0


def test_summarize_empty():
    s = summarize([])
    assert s.total == 0 and s.malformed == 0
    assert s.p50_latency_ms == 0.0 and s.p95_latency_ms == 0.0
    assert s.error_rate == 0.0 and s.top_paths == []


def test_top_paths_limit_and_tiebreak():
    lines = [f"2026-10-01T12:00:00Z GET /p{i} 200 1" for i in range(7)]
    s = summarize(lines)
    assert len(s.top_paths) == 5
    assert [p for p, _ in s.top_paths] == ["/p0", "/p1", "/p2", "/p3", "/p4"]
