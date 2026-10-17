class Inventory:
    def __init__(self):
        self._stock = {}

    def add(self, sku, qty):
        self._stock[sku] = self._stock.get(sku, 0) + qty

    def remove(self, sku, qty):
        if self._stock.get(sku, 0) < qty:
            raise ValueError(f"not enough stock for {sku}")
        self._stock[sku] -= qty

    def count(self, sku):
        return self._stock.get(sku, 0)
