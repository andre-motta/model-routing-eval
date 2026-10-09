"""Parse access log lines and summarize them. See FORMAT.md."""

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone

_METHOD_RE = re.compile(r"[A-Z]+")
_STATUS_RE = re.compile(r"\d{3}")
_LATENCY_RE = re.compile(r"\d+(\.\d+)?")
_BYTES_RE = re.compile(r"\d+")
_TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})")


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


def _parse_timestamp(token: str) -> datetime | None:
    if not _TS_RE.fullmatch(token):
        return None
    try:
        ts = datetime.fromisoformat(token.replace("Z", "+00:00"))
    except ValueError:
        return None
    return ts.astimezone(timezone.utc)


def parse_line(line: str) -> Record | None:
    """Return a Record for a well-formed line, or None if it is malformed."""
    parts = line.split()
    if len(parts) not in (5, 6):
        return None

    ts_tok, method, path, status_tok, latency_tok = parts[:5]
    bytes_tok = parts[5] if len(parts) == 6 else "0"

    ts = _parse_timestamp(ts_tok)
    if ts is None or not _METHOD_RE.fullmatch(method):
        return None
    if not _STATUS_RE.fullmatch(status_tok) or not _LATENCY_RE.fullmatch(latency_tok):
        return None
    if not _BYTES_RE.fullmatch(bytes_tok):
        return None

    latency = float(latency_tok)
    if not math.isfinite(latency):
        return None

    return Record(
        ts=ts,
        method=method,
        path=path,
        status=int(status_tok),
        latency_ms=latency,
        bytes=int(bytes_tok),
    )


def _nearest_rank(sorted_values: list[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    rank = math.ceil(pct / 100 * len(sorted_values))
    return sorted_values[max(rank, 1) - 1]


def summarize(lines) -> Summary:
    """Parse an iterable of lines into a Summary, counting malformed ones."""
    records: list[Record] = []
    malformed = 0
    for line in lines:
        record = parse_line(line)
        if record is None:
            malformed += 1
        else:
            records.append(record)

    by_status = Counter(r.status for r in records)
    by_method = Counter(r.method for r in records)
    path_counts = Counter(r.path for r in records)
    latencies = sorted(r.latency_ms for r in records)
    errors = sum(1 for r in records if r.status >= 500)

    return Summary(
        total=len(records),
        malformed=malformed,
        by_status=dict(by_status),
        by_method=dict(by_method),
        p50_latency_ms=_nearest_rank(latencies, 50),
        p95_latency_ms=_nearest_rank(latencies, 95),
        bytes_total=sum(r.bytes for r in records),
        error_rate=errors / len(records) if records else 0.0,
        top_paths=sorted(path_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:5],
    )
