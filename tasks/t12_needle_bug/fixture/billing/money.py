"""Money helpers. All amounts are Decimal with two places, or int cents."""
from decimal import Decimal, ROUND_HALF_UP

TWO = Decimal("0.01")


def round_money(x: Decimal) -> Decimal:
    return x.quantize(TWO, rounding=ROUND_HALF_UP)


def to_cents(x: Decimal) -> int:
    return int(round_money(x) * 100)


def from_cents(c: int) -> Decimal:
    return Decimal(c) / 100
