"""Webhook helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Webhook:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Webhook":
        self.attrs[key] = value
        return self


def normalize_webhook(items: list[Webhook]) -> list[Webhook]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Webhook] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def webhook_weight(it: Webhook) -> Decimal:
    """Weight used by the webhook ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("1.210")


def describe_webhook(it: Webhook) -> str:
    return f"Webhook({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
