from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from logstats.parse import Record, parse_line, summarize

SAMPLE = Path(__file__).resolve().parents[1] / "sample.log"


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


def test_parse_line_integer_latency():
    record = parse_line("2026-10-01T12:00:01Z POST /api/users 201 40 120")
    assert record is not None
    assert record.latency_ms == 40.0
    assert isinstance(record.latency_ms, float)


def test_timestamp_with_offset_is_converted_to_utc():
    record = parse_line("2026-10-01T14:00:00+02:00 GET /health 200 0.4")
    assert record is not None
    assert record.ts == datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert record.ts.utcoffset() == timedelta(0)


@pytest.mark.parametrize(
    "line",
    [
        "",
        "   ",
        "garbage line here",
        "2026-10-01T12:00:00Z GET /api/users 200",
        "2026-10-01T12:00:00Z GET /api/users 200 12.5 843 extra",
        "not-a-date GET /api/users 200 12.5",
        "2026-10-01T12:00:00 GET /api/users 200 12.5",  # no timezone
        "2026-10-01T12:00:00Z GET /api/users abc 12.5",
        "2026-10-01T12:00:00Z GET /api/users 99 12.5",
        "2026-10-01T12:00:00Z GET /api/users 200 -1.0",
        "2026-10-01T12:00:00Z GET /api/users 200 nan",
        "2026-10-01T12:00:00Z GET /api/users 200 inf",
        "2026-10-01T12:00:00Z GET /api/users 200 1e3",
        "2026-10-01T12:00:00Z GET /api/users 200 12.5 -5",
        "2026-10-01T12:00:00Z GET /api/users 200 12.5 1.5",
    ],
)
def test_malformed_lines_return_none(line):
    assert parse_line(line) is None


def test_summarize_sample_log():
    with SAMPLE.open() as f:
        summary = summarize(f)

    assert summary.total == 5
    assert summary.malformed == 1
    assert summary.by_status == {200: 2, 201: 1, 404: 1, 500: 1}
    assert summary.by_method == {"GET": 4, "POST": 1}
    assert summary.bytes_total == 843 + 120
    assert summary.error_rate == pytest.approx(1 / 5)
    # sorted latencies: 0.4, 3.1, 12.5, 40, 120.0
    assert summary.p50_latency_ms == 12.5
    assert summary.p95_latency_ms == 120.0
    assert summary.top_paths == [("/api/users", 3), ("/api/users/7", 1), ("/health", 1)]


def test_summarize_empty():
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
    assert summary.p50_latency_ms == 0.0


def test_percentiles_are_nearest_rank():
    lines = [
        f"2026-10-01T12:00:00Z GET /x 200 {ms} 0" for ms in range(1, 21)
    ]
    summary = summarize(lines)
    # ceil(0.50 * 20) = 10th value, ceil(0.95 * 20) = 19th value
    assert summary.p50_latency_ms == 10.0
    assert summary.p95_latency_ms == 19.0


def test_error_rate_counts_only_5xx():
    lines = [
        "2026-10-01T12:00:00Z GET /a 404 1",
        "2026-10-01T12:00:00Z GET /a 500 1",
        "2026-10-01T12:00:00Z GET /a 503 1",
        "2026-10-01T12:00:00Z GET /a 200 1",
    ]
    assert summarize(lines).error_rate == 0.5


def test_top_paths_limited_to_five_with_stable_tiebreak():
    paths = ["/e", "/d", "/c", "/b", "/a", "/f", "/g"]
    lines = [f"2026-10-01T12:00:00Z GET {p} 200 1" for p in paths]
    summary = summarize(lines)
    assert summary.top_paths == [("/a", 1), ("/b", 1), ("/c", 1), ("/d", 1), ("/e", 1)]


def test_top_paths_orders_by_count_descending():
    lines = [
        "2026-10-01T12:00:00Z GET /z 200 1",
        "2026-10-01T12:00:00Z GET /z 200 1",
        "2026-10-01T12:00:00Z GET /a 200 1",
    ]
    assert summarize(lines).top_paths == [("/z", 2), ("/a", 1)]
