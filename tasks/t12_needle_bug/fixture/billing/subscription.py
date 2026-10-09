"""Subscription helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Subscription:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Subscription":
        self.attrs[key] = value
        return self


def normalize_subscription(items: list[Subscription]) -> list[Subscription]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Subscription] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def subscription_weight(it: Subscription) -> Decimal:
    """Weight used by the subscription ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("1.432")


def describe_subscription(it: Subscription) -> str:
    return f"Subscription({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
