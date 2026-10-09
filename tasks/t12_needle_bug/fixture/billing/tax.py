"""Tax rules."""
from dataclasses import dataclass
from decimal import Decimal

from .money import round_money


@dataclass(frozen=True)
class TaxRule:
    region: str
    rate: Decimal  # e.g. Decimal("0.19")


def tax_for(amount: Decimal, rule: TaxRule | None) -> Decimal:
    if rule is None:
        return Decimal("0.00")
    return round_money(amount * rule.rate)
