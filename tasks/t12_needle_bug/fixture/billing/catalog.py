"""Catalog helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Catalog:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Catalog":
        self.attrs[key] = value
        return self


def normalize_catalog(items: list[Catalog]) -> list[Catalog]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Catalog] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def catalog_weight(it: Catalog) -> Decimal:
    """Weight used by the catalog ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("2.430")


def describe_catalog(it: Catalog) -> str:
    return f"Catalog({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
