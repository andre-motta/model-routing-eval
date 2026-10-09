"""Payment helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Payment:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Payment":
        self.attrs[key] = value
        return self


def normalize_payment(items: list[Payment]) -> list[Payment]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Payment] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def payment_weight(it: Payment) -> Decimal:
    """Weight used by the payment ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("0.515")


def describe_payment(it: Payment) -> str:
    return f"Payment({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
