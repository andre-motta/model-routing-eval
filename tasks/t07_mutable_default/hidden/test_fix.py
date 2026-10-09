import inspect

from inv.warehouse import Warehouse, Item


def test_independent_warehouses():
    a = Warehouse("a"); a.restock("bolt", 5)
    b = Warehouse("b")
    assert b.report() == {} and b.history == []
    b.restock("nut", 2)
    assert a.report() == {"bolt": 5} and b.report() == {"nut": 2}
    assert a.history == [("restock", "bolt", 5)]


def test_tags_not_shared_between_items():
    w = Warehouse("w")
    w.restock("a", 1); w.restock("b", 1)
    w.stock["a"].tags.append("fragile")
    assert w.stock["b"].tags == []


def test_explicit_stock_still_accepted():
    shared = {}
    w = Warehouse("w", stock=shared)
    w.restock("x", 1)
    assert shared == w.stock and w.report() == {"x": 1}


def test_ship_behaviour_unchanged():
    w = Warehouse("w"); w.restock("x", 3); w.ship("x", 2)
    assert w.report() == {"x": 1}
    try:
        w.ship("x", 5)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_no_mutable_defaults_left():
    for fn in (Warehouse.__init__, Warehouse.restock):
        for p in inspect.signature(fn).parameters.values():
            assert not isinstance(p.default, (list, dict, set)), f"{fn.__qualname__} still has a mutable default"
