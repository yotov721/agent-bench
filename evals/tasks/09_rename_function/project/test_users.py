import unittest

from greeting import greet
from admin import is_admin
from users import get_usr


class Tests(unittest.TestCase):
    def test_lookup(self):
        self.assertEqual(get_usr(1), "ada")

    def test_greet(self):
        self.assertEqual(greet(2), "Hello, grace!")
        self.assertEqual(greet(99), "Hello, stranger!")

    def test_admin(self):
        self.assertTrue(is_admin(1))
        self.assertFalse(is_admin(2))


if __name__ == "__main__":
    unittest.main()
