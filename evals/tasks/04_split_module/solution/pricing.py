TAX_RATE = 0.2


def price_with_tax(net):
    return round(net * (1 + TAX_RATE), 2)


def bulk_discount(qty, unit_price):
    rate = 0.1 if qty >= 10 else 0.0
    return round(qty * unit_price * (1 - rate), 2)
