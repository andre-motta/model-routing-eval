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


def test_total_matches_sum_of_printed_lines_with_discounts():
    # Each line rounds to 0.13 (0.125 half-up), so the printed lines sum to 0.26.
    # The total must match that sum, not the single-rounded 0.25.
    inv = build_invoice("A4", [
        ("a", "0.25", 1, percent_off("HALF", "50")),
        ("b", "0.25", 1, percent_off("HALF", "50")),
    ])
    assert line_totals(inv) == [Decimal("0.13"), Decimal("0.13")]
    assert invoice_total(inv) == sum(line_totals(inv)) == Decimal("0.26")


def test_total_matches_sum_of_printed_lines_with_discounts_and_tax():
    inv = build_invoice("A5", [
        ("a", "0.25", 1, percent_off("HALF", "50")),
        ("b", "0.25", 1, percent_off("HALF", "50")),
    ], TaxRule("DE", Decimal("0.19")))
    # Net is the printed sum 0.26; tax is 0.26 * 0.19 = 0.0494 -> 0.05.
    assert invoice_total(inv) == Decimal("0.31")
