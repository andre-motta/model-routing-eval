"""Meter helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Meter:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Meter":
        self.attrs[key] = value
        return self


def normalize_meter(items: list[Meter]) -> list[Meter]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Meter] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def meter_weight(it: Meter) -> Decimal:
    """Weight used by the meter ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("0.678")


def describe_meter(it: Meter) -> str:
    return f"Meter({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
