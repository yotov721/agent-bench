import json, os, subprocess, sys, tempfile, unittest

TEXT = "hello world\nsecond line here\n"


def run(*args):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(TEXT)
    try:
        return subprocess.run([sys.executable, "wordcount.py", *args, f.name],
                              capture_output=True, text=True, cwd=os.getcwd())
    finally:
        os.unlink(f.name)


class Check(unittest.TestCase):
    def test_json(self):
        r = run("--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout), {"lines": 2, "words": 5, "chars": len(TEXT)})

    def test_default_output_unchanged(self):
        r = run()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, f"lines: 2\nwords: 5\nchars: {len(TEXT)}\n")


unittest.main()
