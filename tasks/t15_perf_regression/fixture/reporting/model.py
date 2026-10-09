from dataclasses import dataclass


@dataclass(frozen=True)
class UsageRow:
    event_id: str
    tenant: str
    service: str
    cpu_seconds: float
    bytes_out: int


def parse_rows(lines):
    """lines: iterable of 'event_id,tenant,service,cpu_seconds,bytes_out'"""
    rows = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        e, t, s, c, b = line.split(",")
        rows.append(UsageRow(e, t, s, float(c), int(b)))
    return rows
