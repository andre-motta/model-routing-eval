"""Refund helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Refund:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Refund":
        self.attrs[key] = value
        return self


def normalize_refund(items: list[Refund]) -> list[Refund]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Refund] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def refund_weight(it: Refund) -> Decimal:
    """Weight used by the refund ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("2.322")


def describe_refund(it: Refund) -> str:
    return f"Refund({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
