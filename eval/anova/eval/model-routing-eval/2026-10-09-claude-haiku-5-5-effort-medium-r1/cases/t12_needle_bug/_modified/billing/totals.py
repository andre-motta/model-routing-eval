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
    """Amount charged: sum of printed line totals, plus tax on that sum."""
    net = sum(line_totals(inv), Decimal("0"))
    return round_money(net + tax_for(net, inv.tax_rule))
