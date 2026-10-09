"""Format support for the reporting pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Format:
    key: str
    value: float = 0.0
    meta: dict = field(default_factory=dict)


def collect_format(items: list[Format]) -> dict[str, float]:
    """Sum values by key. Linear in the number of items."""
    out: dict[str, float] = {}
    for it in items:
        out[it.key] = out.get(it.key, 0.0) + it.value
    return out


def rank_format(totals: dict[str, float], top: int = 10) -> list[tuple[str, float]]:
    return sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
