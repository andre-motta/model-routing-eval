"""Generates the reporting fixture: 40 filler modules plus the real pipeline, one hot path quadratic.
Run once: python generate.py"""
import pathlib
import random

random.seed(99)
root = pathlib.Path(__file__).parent / "fixture"
pkg = root / "reporting"
pkg.mkdir(parents=True, exist_ok=True)
(root / "tests").mkdir(exist_ok=True)

NOUNS = ["tenant", "project", "cluster", "node", "pod", "namespace", "quota", "billing", "alert", "incident",
         "window", "calendar", "holiday", "timezone", "locale", "format", "template", "mailer", "slack", "pager",
         "retention", "archive", "compress", "encrypt", "sign", "verify", "upload", "bucket", "manifest", "index",
         "cache", "throttle", "retry", "backoff", "metric", "trace", "span", "sampler"]
FILLER = '''"""{title} support for the reporting pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class {Cls}:
    key: str
    value: float = 0.0
    meta: dict = field(default_factory=dict)


def collect_{name}(items: list[{Cls}]) -> dict[str, float]:
    """Sum values by key. Linear in the number of items."""
    out: dict[str, float] = {{}}
    for it in items:
        out[it.key] = out.get(it.key, 0.0) + it.value
    return out


def rank_{name}(totals: dict[str, float], top: int = 10) -> list[tuple[str, float]]:
    return sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
'''
for n in NOUNS:
    (pkg / f"{n}.py").write_text(FILLER.format(title=n.title(), Cls=n.title(), name=n))

(pkg / "__init__.py").write_text('''from .model import UsageRow, parse_rows
from .dedupe import dedupe_rows
from .aggregate import aggregate
from .report import build_report

__all__ = ["UsageRow", "parse_rows", "dedupe_rows", "aggregate", "build_report"]
''')
(pkg / "model.py").write_text('''from dataclasses import dataclass


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
''')
# The regression: dedupe keeps a list of seen ids and does `in` on it, O(n^2). Previously a set.
(pkg / "dedupe.py").write_text('''"""Drop duplicate events (the collector retries, so the same event_id can appear several times).

Refactored to keep insertion order of first occurrence, which the old set-based version did not guarantee.
"""


def dedupe_rows(rows):
    seen_ids = []
    out = []
    for r in rows:
        if r.event_id in seen_ids:
            continue
        seen_ids.append(r.event_id)
        out.append(r)
    return out
''')
(pkg / "aggregate.py").write_text('''from collections import defaultdict


def aggregate(rows):
    """Per (tenant, service): total cpu_seconds, total bytes_out, event count. Sorted by tenant then service."""
    acc = defaultdict(lambda: [0.0, 0, 0])
    for r in rows:
        a = acc[(r.tenant, r.service)]
        a[0] += r.cpu_seconds
        a[1] += r.bytes_out
        a[2] += 1
    return {k: tuple(v) for k, v in sorted(acc.items())}
''')
(pkg / "report.py").write_text('''from .dedupe import dedupe_rows
from .aggregate import aggregate


def build_report(rows):
    """Returns list of dicts, one per (tenant, service), plus a totals row at the end."""
    rows = dedupe_rows(rows)
    agg = aggregate(rows)
    out = []
    tot_cpu, tot_bytes, tot_n = 0.0, 0, 0
    for (tenant, service), (cpu, byts, n) in agg.items():
        out.append({"tenant": tenant, "service": service, "cpu_seconds": round(cpu, 3), "bytes_out": byts, "events": n})
        tot_cpu += cpu; tot_bytes += byts; tot_n += n
    out.append({"tenant": "*", "service": "*", "cpu_seconds": round(tot_cpu, 3), "bytes_out": tot_bytes, "events": tot_n})
    return out
''')
(root / "tests" / "test_report.py").write_text('''from reporting import parse_rows, build_report


def test_small_report():
    rows = parse_rows(["e1,acme,api,1.5,100", "e2,acme,api,0.5,50", "e2,acme,api,0.5,50", "e3,beta,web,2,10"])
    rep = build_report(rows)
    assert rep[0] == {"tenant": "acme", "service": "api", "cpu_seconds": 2.0, "bytes_out": 150, "events": 2}
    assert rep[-1]["events"] == 3
''')
(root / "README.md").write_text("# reporting\n\nNightly usage report. `python -m pytest` runs the tests.\n")
print("generated", len(list(pkg.glob("*.py"))), "modules")
