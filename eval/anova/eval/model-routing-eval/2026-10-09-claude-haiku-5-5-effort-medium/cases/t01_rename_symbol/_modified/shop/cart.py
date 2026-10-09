from .pricing import compute_total


class Cart:
    def __init__(self, tax_rate=0.0):
        self.items = []
        self.tax_rate = tax_rate

    def add(self, price, qty=1):
        self.items.append((price, qty))

    def total(self):
        return compute_total(self.items, self.tax_rate)
