"""Debit helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Debit:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Debit":
        self.attrs[key] = value
        return self


def normalize_debit(items: list[Debit]) -> list[Debit]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Debit] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def debit_weight(it: Debit) -> Decimal:
    """Weight used by the debit ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("0.729")


def describe_debit(it: Debit) -> str:
    return f"Debit({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
