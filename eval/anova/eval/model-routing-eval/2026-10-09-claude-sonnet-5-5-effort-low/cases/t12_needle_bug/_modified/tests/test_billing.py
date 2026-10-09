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


def test_total_matches_sum_of_rounded_lines_with_discounts():
    # each line: 1.10 * 0.85 = 0.935 -> 0.94; the old aggregate math gave 2.20 * 0.85 = 1.87
    d = percent_off("D", "15")
    inv = build_invoice("A4", [("x", "1.10", 1, d), ("y", "1.10", 1, d)])
    assert sum(line_totals(inv)) == Decimal("1.88")
    assert invoice_total(inv) == Decimal("1.88")
