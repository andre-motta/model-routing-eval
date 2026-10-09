import pathlib
from decimal import Decimal

from billing import build_invoice, percent_off, invoice_total, line_totals, TaxRule


def test_totals_match_lines_with_discounts():
    # Each line rounds to .xx5 boundaries; per-line rounding vs one-shot rounding disagree by a cent.
    rows = [("a", "1.99", 3, percent_off("P15", "15")),   # 5.97 * 0.85 = 5.0745 -> 5.07
            ("b", "1.99", 3, percent_off("P15", "15"))]   # again 5.07; lines sum 10.14, one-shot 10.149 -> 10.15
    inv = build_invoice("B1", rows)
    assert invoice_total(inv) == sum(line_totals(inv))


def test_many_random_invoices_agree():
    import random
    rnd = random.Random(7)
    for _ in range(300):
        rows = []
        for i in range(rnd.randint(1, 6)):
            price = f"{rnd.randint(1, 9999) / 100:.2f}"
            disc = percent_off("D", str(rnd.choice([5, 7, 12, 15, 33]))) if rnd.random() < 0.6 else None
            rows.append((f"s{i}", price, rnd.randint(1, 9), disc))
        inv = build_invoice("R", rows)
        assert invoice_total(inv) == sum(line_totals(inv)), rows


def test_tax_still_applied_on_net():
    inv = build_invoice("T", [("x", "100.00", 1, percent_off("TEN", "10"))], TaxRule("DE", Decimal("0.19")))
    assert invoice_total(inv) == Decimal("107.10")


def test_regression_test_added():
    tests = pathlib.Path(__file__).resolve().parent.parent / "tests"
    src = "\n".join(p.read_text() for p in tests.glob("test_*.py"))
    assert "line_totals" in src and "invoice_total" in src and "percent_off" in src
    assert src.count("def test_") >= 4, "expected a new regression test under tests/"
