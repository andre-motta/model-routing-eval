"""Parse access logs and summarize them. See FORMAT.md."""
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone

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
    m = _LINE_RE.fullmatch(line.strip())
    if m is None:
        return None
    try:
        ts = datetime.fromisoformat(m["ts"].replace("Z", "+00:00"))
    except ValueError:
        return None
    return Record(
        ts=ts.astimezone(timezone.utc),
        method=m["method"],
        path=m["path"],
        status=int(m["status"]),
        latency_ms=float(m["latency"]),
        bytes=int(m["bytes"] or 0),
    )


def _percentile(sorted_vals: list[float], pct: float) -> float:
    if not sorted_vals:
        return 0.0
    rank = max(1, math.ceil(pct / 100 * len(sorted_vals)))
    return sorted_vals[rank - 1]


def summarize(lines) -> Summary:
    records = []
    malformed = 0
    for line in lines:
        rec = parse_line(line)
        if rec is None:
            malformed += 1
        else:
            records.append(rec)

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
