def line_total(price, qty):
    """Price of `qty` items at `price` each, in dollars rounded to cents."""
    return round(price * qty, 2)


def cart_total(items):
    """Sum of line totals for a list of (price, qty) pairs."""
    return round(sum(line_total(price, qty) for price, qty in items), 2)


def apply_discount(total, percent):
    """Total after taking `percent` percent off."""
    return line_total(total, 1 - percent / 100)
