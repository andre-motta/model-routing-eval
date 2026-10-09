"""Reconcile helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Reconcile:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Reconcile":
        self.attrs[key] = value
        return self


def normalize_reconcile(items: list[Reconcile]) -> list[Reconcile]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Reconcile] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def reconcile_weight(it: Reconcile) -> Decimal:
    """Weight used by the reconcile ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("1.732")


def describe_reconcile(it: Reconcile) -> str:
    return f"Reconcile({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
