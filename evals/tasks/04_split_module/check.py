import ast, os, sys, unittest
sys.path.insert(0, os.getcwd())


def defined_names(path):
    tree = ast.parse(open(path).read())
    return {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}


class Check(unittest.TestCase):
    def test_new_modules_define_the_code(self):
        self.assertTrue({"price_with_tax", "bulk_discount"} <= defined_names("pricing.py"))
        self.assertIn("Inventory", defined_names("inventory.py"))

    def test_shop_no_longer_defines_them(self):
        self.assertFalse({"price_with_tax", "bulk_discount", "Inventory"} & defined_names("shop.py"))

    def test_shop_still_exposes_everything(self):
        from shop import Inventory, bulk_discount, price_with_tax
        self.assertEqual(price_with_tax(10), 12.0)
        self.assertEqual(bulk_discount(10, 5), 45.0)
        self.assertEqual(bulk_discount(2, 5), 10.0)
        inv = Inventory()
        inv.add("a", 3)
        inv.remove("a", 1)
        self.assertEqual(inv.count("a"), 2)
        with self.assertRaises(ValueError):
            inv.remove("a", 5)


unittest.main()
