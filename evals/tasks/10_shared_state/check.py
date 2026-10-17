import copy, os, sys, unittest
sys.path.insert(0, os.getcwd())
import config

PRISTINE = {"debug": False, "retries": 3, "paths": {"cache": "/tmp/cache", "logs": ["/var/log/app"]}}


class Check(unittest.TestCase):
    def test_overrides_dont_leak(self):
        a = config.load_config({"debug": True})
        self.assertTrue(a["debug"])
        self.assertFalse(config.load_config()["debug"])

    def test_nested_mutation_doesnt_leak(self):
        a = config.load_config()
        a["paths"]["logs"].append("/other")
        a["paths"]["cache"] = "/x"
        b = config.load_config()
        self.assertEqual(b["paths"], PRISTINE["paths"])

    def test_defaults_untouched(self):
        config.load_config({"retries": 9})
        config.load_config()["paths"]["logs"].clear()
        self.assertEqual(config.DEFAULTS, PRISTINE)

    def test_override_values_not_aliased(self):
        extra = {"paths": {"cache": "/c", "logs": []}}
        c = config.load_config(extra)
        c["paths"]["logs"].append("x")
        self.assertEqual(extra["paths"]["logs"], [])


unittest.main()
