"""Account helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Account:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Account":
        self.attrs[key] = value
        return self


def normalize_account(items: list[Account]) -> list[Account]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Account] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def account_weight(it: Account) -> Decimal:
    """Weight used by the account ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("2.433")


def describe_account(it: Account) -> str:
    return f"Account({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
