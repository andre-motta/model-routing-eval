"""Parse access logs and summarize them. See FORMAT.md."""

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable

_LINE_RE = re.compile(
    r"(?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))"
    r" (?P<method>[A-Z]+)"
    r" (?P<path>\S+)"
    r" (?P<status>\d{3})"
    r" (?P<latency>\d+(?:\.\d+)?)"
    r"(?: (?P<bytes>\d+))?"
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
    """Return a Record for a well-formed line, or None if it is malformed."""
    match = _LINE_RE.fullmatch(line.rstrip("\r\n"))
    if match is None:
        return None
    raw_ts = match["ts"]
    if raw_ts.endswith("Z"):
        raw_ts = raw_ts[:-1] + "+00:00"
    try:
        ts = datetime.fromisoformat(raw_ts).astimezone(timezone.utc)
    except ValueError:
        return None
    latency = float(match["latency"])
    if not math.isfinite(latency):
        return None
    return Record(
        ts=ts,
        method=match["method"],
        path=match["path"],
        status=int(match["status"]),
        latency_ms=latency,
        bytes=int(match["bytes"] or 0),
    )


def _percentile(sorted_values: list[float], pct: float) -> float:
    """Nearest-rank percentile; 0.0 for empty input."""
    if not sorted_values:
        return 0.0
    rank = max(1, math.ceil(pct / 100 * len(sorted_values)))
    return sorted_values[rank - 1]


def summarize(lines: Iterable[str]) -> Summary:
    records = []
    malformed = 0
    for line in lines:
        record = parse_line(line)
        if record is None:
            malformed += 1
        else:
            records.append(record)

    latencies = sorted(r.latency_ms for r in records)
    paths = Counter(r.path for r in records)
    errors = sum(1 for r in records if r.status >= 500)
    return Summary(
        total=len(records),
        malformed=malformed,
        by_status=dict(Counter(r.status for r in records)),
        by_method=dict(Counter(r.method for r in records)),
        p50_latency_ms=_percentile(latencies, 50),
        p95_latency_ms=_percentile(latencies, 95),
        bytes_total=sum(r.bytes for r in records),
        error_rate=errors / len(records) if records else 0.0,
        top_paths=sorted(paths.items(), key=lambda kv: (-kv[1], kv[0]))[:5],
    )
