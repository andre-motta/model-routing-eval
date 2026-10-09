"""Queue helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Queue:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Queue":
        self.attrs[key] = value
        return self


def normalize_queue(items: list[Queue]) -> list[Queue]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[Queue] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def queue_weight(it: Queue) -> Decimal:
    """Weight used by the queue ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("2.367")


def describe_queue(it: Queue) -> str:
    return f"Queue({it.id}, {it.label!r}, {len(it.attrs)} attrs)"
