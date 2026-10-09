from shop import calc, Cart


def test_calc():
    assert calc([(10, 2), (5, 1)], 0.1) == 27.5


def test_cart():
    c = Cart(0.0)
    c.add(3, 3)
    assert c.total() == 9
