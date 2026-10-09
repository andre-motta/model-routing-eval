import pathlib
import re

import shop
from shop import compute_total, Cart


def test_new_name_works():
    assert compute_total([(10, 2), (5, 1)], 0.1) == 27.5
    c = Cart(0.1); c.add(10, 1)
    assert c.total() == 11.0


def test_old_name_gone_everywhere():
    assert not hasattr(shop, "calc")
    root = pathlib.Path(__file__).resolve().parent.parent
    for p in list(root.rglob("*.py")) + list(root.rglob("*.md")):
        if "hidden" in p.parts or ".git" in p.parts:
            continue
        assert not re.search(r"\bcalc\(", p.read_text()), f"old name still used in {p}"
