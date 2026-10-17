TAX_RATE = 0.2


def price_with_tax(net):
    return round(net * (1 + TAX_RATE), 2)


def bulk_discount(qty, unit_price):
    rate = 0.1 if qty >= 10 else 0.0
    return round(qty * unit_price * (1 - rate), 2)


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
