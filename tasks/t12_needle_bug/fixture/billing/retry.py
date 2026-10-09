"""Retry helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Retry:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Retry":
        self.attrs[key] = value
        return self


def normalize_retry(items: list[Retry]) -> list[Retry]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Retry] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def retry_weight(it: Retry) -> Decimal:
    """Weight used by the retry ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("0.998")


def describe_retry(it: Retry) -> str:
    return f"Retry({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
