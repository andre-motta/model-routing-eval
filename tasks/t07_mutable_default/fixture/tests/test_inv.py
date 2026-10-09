from inv.warehouse import Warehouse


def test_independent_warehouses():
    a = Warehouse("a")
    a.restock("bolt", 5)
    b = Warehouse("b")
    assert b.report() == {}
    b.restock("nut", 2)
    assert a.report() == {"bolt": 5}
    assert len(b.history) == 1
