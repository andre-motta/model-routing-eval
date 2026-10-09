"""Currency helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Currency:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Currency":
        self.attrs[key] = value
        return self


def normalize_currency(items: list[Currency]) -> list[Currency]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Currency] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def currency_weight(it: Currency) -> Decimal:
    """Weight used by the currency ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("2.033")


def describe_currency(it: Currency) -> str:
    return f"Currency({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
