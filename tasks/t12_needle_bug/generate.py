"""Generates the billing fixture: 40 modules of plausible code, one carries the bug.
Run once: python generate.py  (writes ./fixture). Deterministic."""
import pathlib
import random

random.seed(1234)
root = pathlib.Path(__file__).parent / "fixture"
pkg = root / "billing"
(pkg).mkdir(parents=True, exist_ok=True)
(root / "tests").mkdir(exist_ok=True)

NOUNS = ["account", "ledger", "payment", "refund", "statement", "customer", "address", "region", "currency",
         "audit", "schedule", "notify", "export", "importer", "reconcile", "dispute", "credit", "debit", "fee",
         "coupon", "catalog", "product", "plan", "subscription", "usage", "meter", "quota", "limit", "report",
         "archive", "search", "webhook", "retry", "queue"]

FILLER = '''"""{title} helpers for the billing service."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class {Cls}:
    id: str
    label: str = ""
    attrs: dict = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "{Cls}":
        self.attrs[key] = value
        return self


def normalize_{name}(items: list[{Cls}]) -> list[{Cls}]:
    """Stable order by id, drop duplicates, keep the first."""
    seen: set[str] = set()
    out: list[{Cls}] = []
    for it in sorted(items, key=lambda x: x.id):
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def {name}_weight(it: {Cls}) -> Decimal:
    """Weight used by the {name} ranking; purely informational."""
    base = Decimal(len(it.label) or 1)
    return base * Decimal("{factor}")


def describe_{name}(it: {Cls}) -> str:
    return f"{Cls}({{it.id}}, {{it.label!r}}, {{len(it.attrs)}} attrs)"
'''

for n in NOUNS:
    (pkg / f"{n}.py").write_text(FILLER.format(title=n.title(), Cls=n.title(), name=n,
                                               factor=f"{random.uniform(0.5, 2.5):.3f}"))

(pkg / "__init__.py").write_text('''from .invoice import Invoice, LineItem, build_invoice
from .money import to_cents, from_cents, round_money
from .discounts import apply_discount, percent_off, Discount
from .tax import tax_for, TaxRule
from .totals import invoice_total, line_totals

__all__ = ["Invoice", "LineItem", "build_invoice", "to_cents", "from_cents", "round_money",
           "apply_discount", "percent_off", "Discount", "tax_for", "TaxRule", "invoice_total", "line_totals"]
''')

(pkg / "money.py").write_text('''"""Money helpers. All amounts are Decimal with two places, or int cents."""
from decimal import Decimal, ROUND_HALF_UP

TWO = Decimal("0.01")


def round_money(x: Decimal) -> Decimal:
    return x.quantize(TWO, rounding=ROUND_HALF_UP)


def to_cents(x: Decimal) -> int:
    return int(round_money(x) * 100)


def from_cents(c: int) -> Decimal:
    return Decimal(c) / 100
''')

(pkg / "discounts.py").write_text('''"""Discount rules applied per line."""
from dataclasses import dataclass
from decimal import Decimal

from .money import round_money


@dataclass(frozen=True)
class Discount:
    code: str
    percent: Decimal  # 0..100


def percent_off(code: str, pct: str | Decimal) -> Discount:
    return Discount(code, Decimal(pct))


def apply_discount(amount: Decimal, discount: Discount | None) -> Decimal:
    """Return the discounted line amount, rounded to cents."""
    if discount is None:
        return round_money(amount)
    factor = (Decimal(100) - discount.percent) / Decimal(100)
    return round_money(amount * factor)
''')

(pkg / "tax.py").write_text('''"""Tax rules."""
from dataclasses import dataclass
from decimal import Decimal

from .money import round_money


@dataclass(frozen=True)
class TaxRule:
    region: str
    rate: Decimal  # e.g. Decimal("0.19")


def tax_for(amount: Decimal, rule: TaxRule | None) -> Decimal:
    if rule is None:
        return Decimal("0.00")
    return round_money(amount * rule.rate)
''')

(pkg / "invoice.py").write_text('''"""Invoice model."""
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
''')

# The bug: invoice_total discounts the subtotal in one go (rounding once), while the PDF/line view
# discounts each line and rounds per line. The two disagree by a cent when per-line rounding accumulates.
(pkg / "totals.py").write_text('''"""Totals. The PDF renderer shows line_totals(); the amount charged is invoice_total()."""
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
''')

(pkg / "render.py").write_text('''"""Plain-text invoice renderer used by the PDF pipeline."""
from .invoice import Invoice
from .totals import line_totals, invoice_total


def render(inv: Invoice) -> str:
    rows = [f"{li.sku:12} {li.qty:>3} x {li.unit_price:>8}  {amt:>10}" for li, amt in zip(inv.lines, line_totals(inv))]
    rows.append(f"{'TOTAL':>38} {invoice_total(inv):>10}")
    return "\\n".join(rows)
''')

(root / "tests" / "test_billing.py").write_text('''from decimal import Decimal

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
''')
(root / "README.md").write_text("# billing\n\nInternal billing library. Run tests with `python -m pytest`.\n")
print("generated", len(list(pkg.glob('*.py'))), "modules")
