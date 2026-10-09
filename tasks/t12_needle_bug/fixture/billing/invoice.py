"""Invoice model."""
from dataclasses import dataclass, field
from decimal import Decimal

from .discounts import Discount
from .tax import TaxRule


@dataclass
class LineItem:
    sku: str
    unit_price: Decimal
    qty: int
    discount: Discount | None = None


@dataclass
class Invoice:
    number: str
    lines: list[LineItem] = field(default_factory=list)
    tax_rule: TaxRule | None = None

    def add(self, sku: str, unit_price: str | Decimal, qty: int = 1, discount: Discount | None = None) -> "Invoice":
        self.lines.append(LineItem(sku, Decimal(unit_price), qty, discount))
        return self


def build_invoice(number: str, rows: list[tuple], tax_rule: TaxRule | None = None) -> Invoice:
    inv = Invoice(number, tax_rule=tax_rule)
    for row in rows:
        inv.add(*row)
    return inv
