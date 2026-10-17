import unittest

from cart import apply_discount, cart_total, line_total


class CartTests(unittest.TestCase):
    def test_line_total(self):
        self.assertEqual(line_total(19.99, 3), 59.97)

    def test_cart_total(self):
        self.assertEqual(cart_total([(19.99, 3), (4.35, 2)]), 68.67)

    def test_discount(self):
        self.assertEqual(apply_discount(59.97, 10), 53.97)


if __name__ == "__main__":
    unittest.main()
