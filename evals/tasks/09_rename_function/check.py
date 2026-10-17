import glob, os, sys, unittest
sys.path.insert(0, os.getcwd())


class Check(unittest.TestCase):
    def test_no_old_name_left(self):
        for path in glob.glob("*.py"):
            self.assertNotIn("get_usr", open(path).read(), path)

    def test_new_name_works(self):
        from admin import is_admin
        from greeting import greet
        from users import get_user
        self.assertEqual(get_user(3), "linus")
        self.assertIsNone(get_user(42))
        self.assertEqual(greet(1), "Hello, ada!")
        self.assertEqual(greet(0), "Hello, stranger!")
        self.assertTrue(is_admin(1))
        self.assertFalse(is_admin(3))
        self.assertFalse(is_admin(42))

    def test_tests_still_exist(self):
        self.assertTrue(os.path.exists("test_users.py"))
        self.assertIn("get_user", open("test_users.py").read())


unittest.main()
