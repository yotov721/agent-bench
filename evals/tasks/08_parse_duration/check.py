import os, sys, unittest
sys.path.insert(0, os.getcwd())
from duration import parse_duration


class Check(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(parse_duration("45s"), 45)
        self.assertEqual(parse_duration("1h30m"), 5400)
        self.assertEqual(parse_duration(" 2d 4h "), 187200)
        self.assertEqual(parse_duration("1d1h1m1s"), 90061)
        self.assertEqual(parse_duration("0s"), 0)
        self.assertEqual(parse_duration("90m"), 5400)
        self.assertIsInstance(parse_duration("1m"), int)

    def test_invalid(self):
        for bad in ["", "   ", "5x", "h", "10", "1m1h", "1h1h", "1.5h", "-5s", "1h 30", "abc"]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                parse_duration(bad)


unittest.main()
