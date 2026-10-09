"""Statement helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Statement:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Statement":
        self.attrs[key] = value
        return self


def normalize_statement(items: list[Statement]) -> list[Statement]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Statement] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def statement_weight(it: Statement) -> Decimal:
    """Weight used by the statement ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("2.379")


def describe_statement(it: Statement) -> str:
    return f"Statement({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
