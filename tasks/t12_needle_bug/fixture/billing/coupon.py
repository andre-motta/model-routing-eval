"""Coupon helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Coupon:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Coupon":
        self.attrs[key] = value
        return self


def normalize_coupon(items: list[Coupon]) -> list[Coupon]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Coupon] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def coupon_weight(it: Coupon) -> Decimal:
    """Weight used by the coupon ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("1.474")


def describe_coupon(it: Coupon) -> str:
    return f"Coupon({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
