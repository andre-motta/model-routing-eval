"""Parse access log lines and summarize them. See FORMAT.md."""

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone

LINE_RE = re.compile(
    r"^(\S+) ([A-Z]+) (/\S*) (\d{3}) (\d+(?:\.\d+)?)(?: (\d+))?$",
    re.ASCII,
)
MIN_STATUS = 100
MAX_STATUS = 599
TOP_PATHS = 5


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
    by_status: dict[int, int] = field(default_factory=dict)
    by_method: dict[str, int] = field(default_factory=dict)
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    bytes_total: int = 0
    error_rate: float = 0.0
    top_paths: list[tuple[str, int]] = field(default_factory=list)


def parse_line(line: str) -> Record | None:
    """Return the Record for a well-formed line, or None if it is malformed."""
    match = LINE_RE.match(line.strip())
    if match is None:
        return None

    ts_text, method, path, status_text, latency_text, bytes_text = match.groups()
    status = int(status_text)
    if not MIN_STATUS <= status <= MAX_STATUS:
        return None

    if ts_text.endswith("Z"):
        ts_text = ts_text[:-1] + "+00:00"
    try:
        ts = datetime.fromisoformat(ts_text)
    except ValueError:
        return None
    if ts.tzinfo is None:
        return None

    latency_ms = float(latency_text)
    if not math.isfinite(latency_ms):
        return None

    return Record(
        ts=ts.astimezone(timezone.utc),
        method=method,
        path=path,
        status=status,
        latency_ms=latency_ms,
        bytes=int(bytes_text) if bytes_text is not None else 0,
    )


def _nearest_rank(sorted_values: list[float], percent: int) -> float:
    """Nearest-rank percentile of an already sorted, non-empty list."""
    rank = max(1, math.ceil(percent / 100 * len(sorted_values)))
    return sorted_values[rank - 1]


def summarize(lines) -> Summary:
    """Parse every line and aggregate the well-formed records."""
    records = []
    malformed = 0
    for line in lines:
        record = parse_line(line)
        if record is None:
            malformed += 1
        else:
            records.append(record)

    total = len(records)
    if total == 0:
        return Summary(total=0, malformed=malformed)

    latencies = sorted(record.latency_ms for record in records)
    errors = sum(1 for record in records if record.status >= 500)
    path_counts = Counter(record.path for record in records)
    top_paths = sorted(path_counts.items(), key=lambda item: (-item[1], item[0]))

    return Summary(
        total=total,
        malformed=malformed,
        by_status=dict(sorted(Counter(record.status for record in records).items())),
        by_method=dict(sorted(Counter(record.method for record in records).items())),
        p50_latency_ms=_nearest_rank(latencies, 50),
        p95_latency_ms=_nearest_rank(latencies, 95),
        bytes_total=sum(record.bytes for record in records),
        error_rate=errors / total,
        top_paths=top_paths[:TOP_PATHS],
    )
