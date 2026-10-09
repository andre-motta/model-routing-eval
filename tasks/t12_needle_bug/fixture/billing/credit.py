"""Credit helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Credit:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Credit":
        self.attrs[key] = value
        return self


def normalize_credit(items: list[Credit]) -> list[Credit]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Credit] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def credit_weight(it: Credit) -> Decimal:
    """Weight used by the credit ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("0.866")


def describe_credit(it: Credit) -> str:
    return f"Credit({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
