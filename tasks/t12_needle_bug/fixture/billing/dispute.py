"""Dispute helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Dispute:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Dispute":
        self.attrs[key] = value
        return self


def normalize_dispute(items: list[Dispute]) -> list[Dispute]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Dispute] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def dispute_weight(it: Dispute) -> Decimal:
    """Weight used by the dispute ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("0.797")


def describe_dispute(it: Dispute) -> str:
    return f"Dispute({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
