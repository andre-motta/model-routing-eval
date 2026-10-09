"""Usage helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Usage:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Usage":
        self.attrs[key] = value
        return self


def normalize_usage(items: list[Usage]) -> list[Usage]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Usage] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def usage_weight(it: Usage) -> Decimal:
    """Weight used by the usage ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("1.703")


def describe_usage(it: Usage) -> str:
    return f"Usage({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
