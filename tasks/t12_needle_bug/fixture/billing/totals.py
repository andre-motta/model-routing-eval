"""Totals. The PDF renderer shows line_totals(); the amount charged is invoice_total()."""
from decimal import Decimal

from .discounts import apply_discount
from .invoice import Invoice
from .money import round_money
from .tax import tax_for


def line_totals(inv: Invoice) -> list[Decimal]:
    """Per-line amounts as printed on the invoice, discount applied per line."""
    return [apply_discount(li.unit_price * li.qty, li.discount) for li in inv.lines]


def invoice_total(inv: Invoice) -> Decimal:
    """Amount charged: sum of lines after discount, plus tax on that sum."""
    gross = sum((li.unit_price * li.qty for li in inv.lines), Decimal("0"))
    discount_amount = Decimal("0")
    for li in inv.lines:
        if li.discount is not None:
            discount_amount += li.unit_price * li.qty * li.discount.percent / Decimal(100)
    net = round_money(gross - discount_amount)
    return round_money(net + tax_for(net, inv.tax_rule))
