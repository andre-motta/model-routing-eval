import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from logstats.parse import parse_line, summarize

SAMPLE = Path(__file__).resolve().parent.parent / "sample.log"


class ParseLineTests(unittest.TestCase):
    def test_full_line(self):
        r = parse_line("2026-10-01T12:00:00Z GET /api/users 200 12.5 843")
        self.assertEqual(r.ts, datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(r.method, "GET")
        self.assertEqual(r.path, "/api/users")
        self.assertEqual(r.status, 200)
        self.assertEqual(r.latency_ms, 12.5)
        self.assertEqual(r.bytes, 843)

    def test_missing_bytes_defaults_to_zero(self):
        r = parse_line("2026-10-01T12:00:02Z GET /api/users/7 404 3.1")
        self.assertEqual(r.bytes, 0)
        self.assertEqual(r.status, 404)

    def test_integer_latency(self):
        r = parse_line("2026-10-01T12:00:01Z POST /api/users 201 40 120")
        self.assertEqual(r.latency_ms, 40.0)

    def test_offset_timestamp_converted_to_utc(self):
        r = parse_line("2026-10-01T14:00:00+02:00 GET / 200 1 0")
        self.assertEqual(r.ts.utcoffset(), timedelta(0))
        self.assertEqual(r.ts.hour, 12)

    def test_malformed_lines(self):
        bad = [
            "",
            "garbage line here",
            "2026-10-01T12:00:00Z GET /x 200",  # missing latency
            "2026-10-01T12:00:00Z GET /x abc 1.0",  # non-int status
            "2026-10-01T12:00:00Z GET /x 200 fast",  # non-float latency
            "2026-10-01T12:00:00Z GET /x 200 1.0 12 extra",  # trailing junk
            "2026-10-01T12:00:00 GET /x 200 1.0",  # no timezone
            "not-a-date GET /x 200 1.0",  # bad timestamp
        ]
        for line in bad:
            with self.subTest(line=line):
                self.assertIsNone(parse_line(line))


class SummarizeTests(unittest.TestCase):
    def test_sample_log(self):
        with SAMPLE.open() as fh:
            s = summarize(fh)
        self.assertEqual(s.total, 5)
        self.assertEqual(s.malformed, 1)
        self.assertEqual(s.by_status, {200: 2, 201: 1, 404: 1, 500: 1})
        self.assertEqual(s.by_method, {"GET": 4, "POST": 1})
        self.assertEqual(s.bytes_total, 963)
        self.assertAlmostEqual(s.error_rate, 0.2)
        # sorted latencies: 0.4, 3.1, 12.5, 40, 120.0
        self.assertEqual(s.p50_latency_ms, 12.5)
        self.assertEqual(s.p95_latency_ms, 120.0)
        self.assertEqual(
            s.top_paths,
            [("/api/users", 3), ("/api/users/7", 1), ("/health", 1)],
        )

    def test_empty_input(self):
        s = summarize([])
        self.assertEqual(s.total, 0)
        self.assertEqual(s.malformed, 0)
        self.assertEqual(s.p50_latency_ms, 0.0)
        self.assertEqual(s.p95_latency_ms, 0.0)
        self.assertEqual(s.error_rate, 0.0)
        self.assertEqual(s.top_paths, [])

    def test_all_malformed(self):
        s = summarize(["junk", "more junk"])
        self.assertEqual(s.total, 0)
        self.assertEqual(s.malformed, 2)
        self.assertEqual(s.by_status, {})

    def test_nearest_rank_percentiles(self):
        lines = [
            f"2026-10-01T12:00:00Z GET /p 200 {ms} 0" for ms in range(1, 101)
        ]
        s = summarize(lines)
        self.assertEqual(s.p50_latency_ms, 50.0)
        self.assertEqual(s.p95_latency_ms, 95.0)

    def test_top_paths_tie_broken_by_path_and_capped_at_five(self):
        paths = ["/c", "/a", "/b", "/d", "/e", "/f"]
        lines = [f"2026-10-01T12:00:00Z GET {p} 200 1 0" for p in paths]
        s = summarize(lines)
        self.assertEqual(s.top_paths, [("/a", 1), ("/b", 1), ("/c", 1), ("/d", 1), ("/e", 1)])

    def test_error_rate_counts_5xx_only(self):
        lines = [
            "2026-10-01T12:00:00Z GET /a 503 1 0",
            "2026-10-01T12:00:00Z GET /a 499 1 0",
        ]
        self.assertEqual(summarize(lines).error_rate, 0.5)


if __name__ == "__main__":
    unittest.main()
