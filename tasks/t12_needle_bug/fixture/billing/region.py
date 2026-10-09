"""Region helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Region:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Region":
        self.attrs[key] = value
        return self


def normalize_region(items: list[Region]) -> list[Region]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Region] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def region_weight(it: Region) -> Decimal:
    """Weight used by the region ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("0.668")


def describe_region(it: Region) -> str:
    return f"Region({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
