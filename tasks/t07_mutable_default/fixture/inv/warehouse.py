from dataclasses import dataclass, field


@dataclass
class Item:
    sku: str
    qty: int = 0
    tags: list = field(default_factory=list)


class Warehouse:
    def __init__(self, name, stock={}, history=[]):
        self.name = name
        self.stock = stock
        self.history = history

    def restock(self, sku, qty, tags=[]):
        item = self.stock.get(sku)
        if item is None:
            item = Item(sku, 0, tags)
            self.stock[sku] = item
        item.qty += qty
        self.history.append(("restock", sku, qty))

    def ship(self, sku, qty):
        item = self.stock[sku]
        if item.qty < qty:
            raise ValueError("insufficient stock")
        item.qty -= qty
        self.history.append(("ship", sku, qty))

    def report(self):
        return {sku: item.qty for sku, item in sorted(self.stock.items())}
