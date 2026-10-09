from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from logstats.parse import Record, parse_line, summarize

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "sample.log"


def test_parse_line_with_bytes():
    record = parse_line("2026-10-01T12:00:00Z GET /api/users 200 12.5 843")
    assert record == Record(
        ts=datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc),
        method="GET",
        path="/api/users",
        status=200,
        latency_ms=12.5,
        bytes=843,
    )


def test_parse_line_without_bytes_defaults_to_zero():
    record = parse_line("2026-10-01T12:00:02Z GET /api/users/7 404 3.1")
    assert record is not None
    assert record.status == 404
    assert record.latency_ms == 3.1
    assert record.bytes == 0


def test_parse_line_converts_offset_to_utc():
    record = parse_line("2026-10-01T14:00:00+02:00 GET / 200 1")
    assert record is not None
    assert record.ts == datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert record.ts.utcoffset() == timedelta(0)


def test_parse_line_tolerates_trailing_newline():
    assert parse_line("2026-10-01T12:00:00Z GET /health 200 0.4\n") is not None


@pytest.mark.parametrize(
    "line",
    [
        "",
        "garbage line here",
        "2026-10-01T12:00:00Z GET /api/users 200",  # missing latency
        "2026-10-01T12:00:00Z GET /api/users 200 12.5 843 extra",  # too many fields
        "not-a-time GET /api/users 200 12.5",
        "2026-10-01T12:00:00 GET /api/users 200 12.5",  # naive timestamp, no zone
        "2026-10-01T12:00:00Z get /api/users 200 12.5",  # lowercase method
        "2026-10-01T12:00:00Z GET api/users 200 12.5",  # path without leading slash
        "2026-10-01T12:00:00Z GET /api/users two-hundred 12.5",
        "2026-10-01T12:00:00Z GET /api/users 99 12.5",  # status below 100
        "2026-10-01T12:00:00Z GET /api/users 200 fast",
        "2026-10-01T12:00:00Z GET /api/users 200 nan",
        "2026-10-01T12:00:00Z GET /api/users 200 -1",
        "2026-10-01T12:00:00Z GET /api/users 200 12.5 -5",
        "2026-10-01T12:00:00Z GET /api/users 200 12.5 1.5",
    ],
)
def test_parse_line_rejects_malformed(line):
    assert parse_line(line) is None


def test_summarize_sample_log():
    with SAMPLE.open() as handle:
        summary = summarize(handle)

    assert summary.total == 5
    assert summary.malformed == 1
    assert summary.by_status == {200: 2, 201: 1, 404: 1, 500: 1}
    assert summary.by_method == {"GET": 4, "POST": 1}
    assert summary.bytes_total == 843 + 120
    assert summary.error_rate == pytest.approx(1 / 5)
    assert summary.top_paths == [("/api/users", 3), ("/api/users/7", 1), ("/health", 1)]


def test_summarize_percentiles_use_nearest_rank():
    latencies = [5, 1, 4, 2, 3, 10, 7, 8, 9, 6]
    lines = [
        f"2026-10-01T12:00:00Z GET /x 200 {value}" for value in latencies
    ]
    summary = summarize(lines)
    # Sorted: 1..10. p50 -> rank 5 -> 5. p95 -> rank ceil(9.5)=10 -> 10.
    assert summary.p50_latency_ms == 5
    assert summary.p95_latency_ms == 10


def test_summarize_top_paths_limited_and_tie_broken_by_path():
    lines = []
    for path in ["/c", "/a", "/b", "/d", "/e", "/f"]:
        lines.append(f"2026-10-01T12:00:00Z GET {path} 200 1")
    lines.append("2026-10-01T12:00:00Z GET /z 200 1")
    lines.append("2026-10-01T12:00:00Z GET /z 200 1")
    summary = summarize(lines)
    assert summary.top_paths == [("/z", 2), ("/a", 1), ("/b", 1), ("/c", 1), ("/d", 1)]


def test_summarize_empty_input():
    summary = summarize([])
    assert summary.total == 0
    assert summary.malformed == 0
    assert summary.by_status == {}
    assert summary.by_method == {}
    assert summary.p50_latency_ms == 0.0
    assert summary.p95_latency_ms == 0.0
    assert summary.bytes_total == 0
    assert summary.error_rate == 0.0
    assert summary.top_paths == []


def test_summarize_all_malformed():
    summary = summarize(["junk", "more junk"])
    assert summary.total == 0
    assert summary.malformed == 2
    assert summary.error_rate == 0.0
    assert summary.p95_latency_ms == 0.0
