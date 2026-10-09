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


def test_total_matches_sum_of_printed_lines_with_half_cent_discounts():
    # Each line discounts to 1.125, which prints as 1.13. The total must
    # equal the printed lines (2.26), not the unrounded discount (2.25).
    inv = build_invoice("A4", [
        ("a", "1.25", 1, percent_off("TEN", "10")),
        ("b", "1.25", 1, percent_off("TEN", "10")),
    ])
    assert line_totals(inv) == [Decimal("1.13"), Decimal("1.13")]
    assert invoice_total(inv) == sum(line_totals(inv)) == Decimal("2.26")


def test_total_matches_sum_of_printed_lines_with_tax():
    inv = build_invoice("A5", [
        ("a", "1.25", 1, percent_off("TEN", "10")),
        ("b", "1.25", 1, percent_off("TEN", "10")),
    ], TaxRule("DE", Decimal("0.19")))
    net = sum(line_totals(inv))
    assert invoice_total(inv) == (net + net * Decimal("0.19")).quantize(Decimal("0.01"))
