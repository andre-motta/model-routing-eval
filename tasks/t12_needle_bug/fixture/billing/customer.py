"""Customer helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Customer:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Customer":
        self.attrs[key] = value
        return self


def normalize_customer(items: list[Customer]) -> list[Customer]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Customer] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def customer_weight(it: Customer) -> Decimal:
    """Weight used by the customer ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("1.664")


def describe_customer(it: Customer) -> str:
    return f"Customer({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
