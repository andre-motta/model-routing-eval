"""Audit helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Audit:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Audit":
        self.attrs[key] = value
        return self


def normalize_audit(items: list[Audit]) -> list[Audit]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Audit] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def audit_weight(it: Audit) -> Decimal:
    """Weight used by the audit ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("0.974")


def describe_audit(it: Audit) -> str:
    return f"Audit({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
