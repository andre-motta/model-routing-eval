"""Parse access log lines and summarize them. See FORMAT.md."""

import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

_STATUS_RE = re.compile(r"[1-5][0-9]{2}")
_LATENCY_RE = re.compile(r"[0-9]+(?:\.[0-9]+)?")
_BYTES_RE = re.compile(r"[0-9]+")


@dataclass
class Record:
    ts: datetime
    method: str
    path: str
    status: int
    latency_ms: float
    bytes: int


@dataclass
class Summary:
    total: int
    malformed: int
    by_status: dict[int, int]
    by_method: dict[str, int]
    p50_latency_ms: float
    p95_latency_ms: float
    bytes_total: int
    error_rate: float
    top_paths: list[tuple[str, int]]


def parse_line(line: str) -> Record | None:
    """Return the Record for a log line, or None if the line is malformed."""
    parts = line.split()
    if len(parts) not in (5, 6):
        return None

    ts_text, method, path, status_text, latency_text, *rest = parts
    bytes_text = rest[0] if rest else "0"
    if not (
        _STATUS_RE.fullmatch(status_text)
        and _LATENCY_RE.fullmatch(latency_text)
        and _BYTES_RE.fullmatch(bytes_text)
    ):
        return None

    try:
        ts = datetime.fromisoformat(ts_text)
    except ValueError:
        return None
    if ts.tzinfo is None:
        return None

    return Record(
        ts=ts.astimezone(timezone.utc),
        method=method,
        path=path,
        status=int(status_text),
        latency_ms=float(latency_text),
        bytes=int(bytes_text),
    )


def _percentile(sorted_values: list[float], pct: int) -> float:
    """Nearest-rank percentile over already-sorted values; 0.0 if empty."""
    if not sorted_values:
        return 0.0
    rank = math.ceil(pct * len(sorted_values) / 100)
    return sorted_values[rank - 1]


def summarize(lines: Iterable[str]) -> Summary:
    """Aggregate log lines, counting malformed lines instead of failing on them."""
    records: list[Record] = []
    malformed = 0
    for line in lines:
        record = parse_line(line)
        if record is None:
            malformed += 1
        else:
            records.append(record)

    total = len(records)
    latencies = sorted(r.latency_ms for r in records)
    errors = sum(1 for r in records if r.status >= 500)
    path_counts = Counter(r.path for r in records)

    return Summary(
        total=total,
        malformed=malformed,
        by_status=dict(sorted(Counter(r.status for r in records).items())),
        by_method=dict(sorted(Counter(r.method for r in records).items())),
        p50_latency_ms=_percentile(latencies, 50),
        p95_latency_ms=_percentile(latencies, 95),
        bytes_total=sum(r.bytes for r in records),
        error_rate=errors / total if total else 0.0,
        top_paths=sorted(path_counts.items(), key=lambda item: (-item[1], item[0]))[:5],
    )
