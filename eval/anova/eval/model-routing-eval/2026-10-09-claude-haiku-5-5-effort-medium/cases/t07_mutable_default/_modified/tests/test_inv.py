from inv.warehouse import Warehouse


def test_independent_warehouses():
    a = Warehouse("a")
    a.restock("bolt", 5)
    b = Warehouse("b")
    assert b.report() == {}
    b.restock("nut", 2)
    assert a.report() == {"bolt": 5}
    assert len(b.history) == 1


def test_restock_tags_not_shared():
    a = Warehouse("a")
    a.restock("bolt", 1, tags=["metal"])
    b = Warehouse("b")
    b.restock("nut", 1)
    assert a.stock["bolt"].tags == ["metal"]
    assert b.stock["nut"].tags == []
    assert a.stock["bolt"].tags is not b.stock["nut"].tags
