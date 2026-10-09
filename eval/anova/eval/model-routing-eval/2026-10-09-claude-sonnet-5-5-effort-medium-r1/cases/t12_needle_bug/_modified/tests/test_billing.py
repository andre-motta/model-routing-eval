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


def test_total_matches_printed_lines_with_discounts():
    # Each line is 0.05 * 7% off = 4.65 -> rounds per line; unrounded sum differs by a cent.
    rows = [("a", "0.05", 1, percent_off("D", "7"))] * 10 + [("b", "1.35", 1, percent_off("D", "15"))] * 3
    inv = build_invoice("A4", rows)
    assert invoice_total(inv) == sum(line_totals(inv))


def test_total_matches_lines_half_cent_discounts():
    inv = build_invoice("A5", [("a", "0.10", 1, percent_off("D", "5"))] * 3)
    # each line 0.095 -> 0.10 (half up); printed sum 0.30, unrounded 0.285 -> 0.29
    assert sum(line_totals(inv)) == Decimal("0.30")
    assert invoice_total(inv) == Decimal("0.30")
