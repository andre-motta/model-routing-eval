"""Limit helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Limit:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Limit":
        self.attrs[key] = value
        return self


def normalize_limit(items: list[Limit]) -> list[Limit]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Limit] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def limit_weight(it: Limit) -> Decimal:
    """Weight used by the limit ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("1.039")


def describe_limit(it: Limit) -> str:
    return f"Limit({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
