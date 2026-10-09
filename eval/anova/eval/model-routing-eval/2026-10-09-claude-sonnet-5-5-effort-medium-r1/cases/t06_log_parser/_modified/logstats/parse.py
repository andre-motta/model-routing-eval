"""Parse access logs and summarize them. See FORMAT.md."""
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable

_INT = re.compile(r"\d+")
_FLOAT = re.compile(r"\d+(?:\.\d+)?|\.\d+")
_METHOD = re.compile(r"[A-Z]+")


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


def _parse_ts(text: str) -> datetime | None:
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    try:
        ts = datetime.fromisoformat(text)
    except ValueError:
        return None
    if ts.tzinfo is None:
        return None
    return ts.astimezone(timezone.utc)


def parse_line(line: str) -> Record | None:
    """Parse one log line; return None if it is malformed."""
    parts = line.split()
    if len(parts) not in (5, 6):
        return None
    ts_s, method, path, status_s, latency_s, *rest = parts
    bytes_s = rest[0] if rest else "0"

    ts = _parse_ts(ts_s)
    if ts is None or not _METHOD.fullmatch(method):
        return None
    if not (_INT.fullmatch(status_s) and _FLOAT.fullmatch(latency_s) and _INT.fullmatch(bytes_s)):
        return None
    return Record(ts, method, path, int(status_s), float(latency_s), int(bytes_s))


def _percentile(sorted_vals: list[float], pct: float) -> float:
    """Nearest-rank percentile."""
    if not sorted_vals:
        return 0.0
    rank = max(1, math.ceil(pct / 100 * len(sorted_vals)))
    return sorted_vals[rank - 1]


def summarize(lines: Iterable[str]) -> Summary:
    records = []
    malformed = 0
    for line in lines:
        if not line.strip():
            continue
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
