"""Ledger helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Ledger:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Ledger":
        self.attrs[key] = value
        return self


def normalize_ledger(items: list[Ledger]) -> list[Ledger]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Ledger] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def ledger_weight(it: Ledger) -> Decimal:
    """Weight used by the ledger ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("1.381")


def describe_ledger(it: Ledger) -> str:
    return f"Ledger({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
