import os, sys, unittest
sys.path.insert(0, os.getcwd())
import stats


class Check(unittest.TestCase):
    def test_empty(self):
        self.assertIsNone(stats.mean([]))
        self.assertIsNone(stats.median([]))
        self.assertIsNone(stats.maximum([]))

    def test_non_empty_unchanged(self):
        self.assertEqual(stats.mean([1, 2, 3, 4]), 2.5)
        self.assertEqual(stats.median([3, 1, 2]), 2)
        self.assertEqual(stats.median([4, 1, 3, 2]), 2.5)
        self.assertEqual(stats.maximum([-5, -2, -9]), -2)

    def test_zero_is_not_empty(self):
        self.assertEqual(stats.mean([0]), 0)
        self.assertEqual(stats.maximum([0]), 0)


unittest.main()
