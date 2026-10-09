"""Export helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Export:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Export":
        self.attrs[key] = value
        return self


def normalize_export(items: list[Export]) -> list[Export]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Export] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def export_weight(it: Export) -> Decimal:
    """Weight used by the export ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("1.192")


def describe_export(it: Export) -> str:
    return f"Export({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
