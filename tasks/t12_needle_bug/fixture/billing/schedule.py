"""Schedule helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Schedule:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Schedule":
        self.attrs[key] = value
        return self


def normalize_schedule(items: list[Schedule]) -> list[Schedule]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Schedule] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def schedule_weight(it: Schedule) -> Decimal:
    """Weight used by the schedule ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("0.562")


def describe_schedule(it: Schedule) -> str:
    return f"Schedule({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
