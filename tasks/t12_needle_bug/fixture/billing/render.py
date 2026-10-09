"""Plain-text invoice renderer used by the PDF pipeline."""
from .invoice import Invoice
from .totals import line_totals, invoice_total


def render(inv: Invoice) -> str:
    rows = [f"{li.sku:12} {li.qty:>3} x {li.unit_price:>8}  {amt:>10}" for li, amt in zip(inv.lines, line_totals(inv))]
    rows.append(f"{'TOTAL':>38} {invoice_total(inv):>10}")
    return "\n".join(rows)
