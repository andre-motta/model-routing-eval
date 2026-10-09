from decimal import Decimal

from billing import build_invoice, percent_off, invoice_total, line_totals, TaxRule


def test_simple_total():
    inv = build_invoice("A1", [("x", "10.00", 2), ("y", "0.50", 1)])
    assert invoice_total(inv) == Decimal("20.50")
    assert sum(line_totals(inv)) == Decimal("20.50")


def test_with_tax():
    inv = build_invoice("A2", [("x", "100.00", 1)], TaxRule("DE", Decimal("0.19")))
    assert invoice_total(inv) == Decimal("119.00")


def test_discount_whole_numbers():
    inv = build_invoice("A3", [("x", "100.00", 1, percent_off("TEN", "10"))])
    assert invoice_total(inv) == Decimal("90.00")


def test_total_matches_printed_line_items_with_discounts():
    # 10.05 * 90% = 9.045 -> 9.05 per line; unrounded sum 18.09 would differ from printed 18.10
    inv = build_invoice("A4", [("x", "10.05", 1, percent_off("TEN", "10")),
                               ("y", "10.05", 1, percent_off("TEN", "10"))])
    assert line_totals(inv) == [Decimal("9.05"), Decimal("9.05")]
    assert invoice_total(inv) == sum(line_totals(inv)) == Decimal("18.10")
