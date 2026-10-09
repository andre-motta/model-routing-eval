# Access log format

One request per line:

```
<ISO-8601 timestamp> <METHOD> <path> <status> <latency_ms> [<bytes>]
2026-10-01T12:00:00Z GET /api/users 200 12.5 843
2026-10-01T12:00:01Z POST /api/users 201 40 120
2026-10-01T12:00:02Z GET /api/users/7 404 3.1
```

- `bytes` is optional; treat missing as 0.
- `latency_ms` is a float, `status` and `bytes` are ints.
- Any line that does not match is malformed.

`Record` is a dataclass with fields `ts: datetime` (timezone-aware UTC), `method: str`,
`path: str`, `status: int`, `latency_ms: float`, `bytes: int`.

`Summary` is a dataclass with:
- `total: int` parsed records
- `malformed: int`
- `by_status: dict[int, int]`
- `by_method: dict[str, int]`
- `p50_latency_ms: float`, `p95_latency_ms: float` (nearest-rank percentile over parsed records, 0.0 if none)
- `bytes_total: int`
- `error_rate: float` share of records with status >= 500, 0.0 if none
- `top_paths: list[tuple[str, int]]` five most frequent paths, count descending then path ascending
