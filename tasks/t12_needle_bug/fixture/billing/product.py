"""Product helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Product:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Product":
        self.attrs[key] = value
        return self


def normalize_product(items: list[Product]) -> list[Product]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Product] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def product_weight(it: Product) -> Decimal:
    """Weight used by the product ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("0.629")


def describe_product(it: Product) -> str:
    return f"Product({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
