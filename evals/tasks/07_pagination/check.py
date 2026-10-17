import os, sys, unittest
sys.path.insert(0, os.getcwd())
from paginate import paginate, total_pages


class Check(unittest.TestCase):
    def test_total_pages(self):
        self.assertEqual(total_pages(0, 10), 0)
        self.assertEqual(total_pages(10, 10), 1)
        self.assertEqual(total_pages(11, 10), 2)
        self.assertEqual(total_pages(25, 10), 3)
        self.assertEqual(total_pages(1, 3), 1)

    def test_pages(self):
        items = list(range(1, 8))
        self.assertEqual(paginate(items, 1, 3), [1, 2, 3])
        self.assertEqual(paginate(items, 2, 3), [4, 5, 6])
        self.assertEqual(paginate(items, 3, 3), [7])

    def test_past_end(self):
        self.assertEqual(paginate([1, 2, 3], 2, 3), [])
        self.assertEqual(paginate([], 1, 5), [])

    def test_invalid_page(self):
        with self.assertRaises(ValueError):
            paginate([1], 0, 1)


unittest.main()
