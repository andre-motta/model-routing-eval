"""Report helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Report:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Report":
        self.attrs[key] = value
        return self


def normalize_report(items: list[Report]) -> list[Report]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Report] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def report_weight(it: Report) -> Decimal:
    """Weight used by the report ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("1.613")


def describe_report(it: Report) -> str:
    return f"Report({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
