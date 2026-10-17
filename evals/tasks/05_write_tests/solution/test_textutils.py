import unittest

from textutils import slugify, truncate, wrap_words


class SlugifyTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_punctuation_runs_collapse(self):
        self.assertEqual(slugify("a -- b!!c"), "a-b-c")

    def test_strips_edges(self):
        self.assertEqual(slugify("  --Hi--  "), "hi")

    def test_uppercase(self):
        self.assertEqual(slugify("ABC"), "abc")

    def test_empty(self):
        self.assertEqual(slugify(""), "")


class TruncateTests(unittest.TestCase):
    def test_short_unchanged(self):
        self.assertEqual(truncate("hello", 10), "hello")

    def test_exact_limit_unchanged(self):
        self.assertEqual(truncate("hello", 5), "hello")

    def test_cut_with_suffix_is_exact_limit(self):
        out = truncate("hello world", 8)
        self.assertEqual(out, "hello...")
        self.assertEqual(len(out), 8)

    def test_custom_suffix(self):
        self.assertEqual(truncate("hello world", 7, suffix="~"), "hello ~")


class WrapTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(wrap_words("aaa bbb ccc", 7), ["aaa bbb", "ccc"])

    def test_exact_width_fits(self):
        self.assertEqual(wrap_words("aa bb", 5), ["aa bb"])

    def test_long_word_own_line(self):
        self.assertEqual(wrap_words("hi extraordinary yo", 5), ["hi", "extraordinary", "yo"])

    def test_empty(self):
        self.assertEqual(wrap_words("", 5), [])

    def test_last_line_kept(self):
        self.assertEqual(wrap_words("a b c", 1), ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
