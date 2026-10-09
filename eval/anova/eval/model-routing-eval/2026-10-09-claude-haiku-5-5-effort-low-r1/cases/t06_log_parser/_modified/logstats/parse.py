"""Parser and summary for the access log format described in FORMAT.md."""

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone

LINE_RE = re.compile(
    r"(?P<ts>\S+) (?P<method>[A-Z]+) (?P<path>\S+) (?P<status>\d+) "
    r"(?P<latency>\d+(?:\.\d+)?)(?: (?P<bytes>\d+))?"
)


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
    total: int = 0
    malformed: int = 0
    by_status: dict[int, int] = field(default_factory=dict)
    by_method: dict[str, int] = field(default_factory=dict)
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    bytes_total: int = 0
    error_rate: float = 0.0
    top_paths: list[tuple[str, int]] = field(default_factory=list)


def parse_line(line: str) -> Record | None:
    """Return a Record for a well-formed line, or None if the line is malformed."""
    match = LINE_RE.fullmatch(line.rstrip("\r\n"))
    if match is None:
        return None
    try:
        ts = datetime.fromisoformat(match["ts"])
    except ValueError:
        return None
    if ts.tzinfo is None:
        return None
    return Record(
        ts=ts.astimezone(timezone.utc),
        method=match["method"],
        path=match["path"],
        status=int(match["status"]),
        latency_ms=float(match["latency"]),
        bytes=int(match["bytes"] or 0),
    )


def _nearest_rank(sorted_values: list[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    rank = math.ceil(pct / 100 * len(sorted_values))
    return sorted_values[max(rank, 1) - 1]


def summarize(lines) -> Summary:
    """Parse an iterable of log lines into a Summary, counting malformed lines."""
    records: list[Record] = []
    malformed = 0
    for line in lines:
        record = parse_line(line)
        if record is None:
            malformed += 1
        else:
            records.append(record)

    latencies = sorted(r.latency_ms for r in records)
    by_status = Counter(r.status for r in records)
    by_method = Counter(r.method for r in records)
    paths = Counter(r.path for r in records)
    server_errors = sum(1 for r in records if r.status >= 500)

    return Summary(
        total=len(records),
        malformed=malformed,
        by_status=dict(by_status),
        by_method=dict(by_method),
        p50_latency_ms=_nearest_rank(latencies, 50),
        p95_latency_ms=_nearest_rank(latencies, 95),
        bytes_total=sum(r.bytes for r in records),
        error_rate=server_errors / len(records) if records else 0.0,
        top_paths=sorted(paths.items(), key=lambda kv: (-kv[1], kv[0]))[:5],
    )
