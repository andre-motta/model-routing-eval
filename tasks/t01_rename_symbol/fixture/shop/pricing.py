def calc(items, tax_rate=0.0):
    """Return the total price of items with tax applied.

    items: iterable of (unit_price, quantity)
    """
    subtotal = sum(price * qty for price, qty in items)
    return round(subtotal * (1 + tax_rate), 2)
