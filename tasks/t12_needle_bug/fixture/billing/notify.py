"""Notify helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Notify:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Notify":
        self.attrs[key] = value
        return self


def normalize_notify(items: list[Notify]) -> list[Notify]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Notify] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def notify_weight(it: Notify) -> Decimal:
    """Weight used by the notify ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("2.078")


def describe_notify(it: Notify) -> str:
    return f"Notify({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
