from dataclasses import dataclass, field


@dataclass
class Item:
    sku: str
    qty: int = 0
    tags: list = field(default_factory=list)


class Warehouse:
    def __init__(self, name, stock=None, history=None):
        self.name = name
        self.stock = stock if stock is not None else {}
        self.history = history if history is not None else []

    def restock(self, sku, qty, tags=None):
        item = self.stock.get(sku)
        if item is None:
            item = Item(sku, 0, list(tags) if tags is not None else [])
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
