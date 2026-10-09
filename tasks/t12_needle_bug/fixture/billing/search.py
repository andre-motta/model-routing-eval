"""Search helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Search:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Search":
        self.attrs[key] = value
        return self


def normalize_search(items: list[Search]) -> list[Search]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Search] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def search_weight(it: Search) -> Decimal:
    """Weight used by the search ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("1.462")


def describe_search(it: Search) -> str:
    return f"Search({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
