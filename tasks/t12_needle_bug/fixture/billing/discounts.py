"""Discount rules applied per line."""
from dataclasses import dataclass
from decimal import Decimal

from .money import round_money


@dataclass(frozen=True)
class Discount:
    code: str
    percent: Decimal  # 0..100


def percent_off(code: str, pct: str | Decimal) -> Discount:
    return Discount(code, Decimal(pct))


def apply_discount(amount: Decimal, discount: Discount | None) -> Decimal:
    """Return the discounted line amount, rounded to cents."""
    if discount is None:
        return round_money(amount)
    factor = (Decimal(100) - discount.percent) / Decimal(100)
    return round_money(amount * factor)
