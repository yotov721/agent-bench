"""Pass if the agent's tests pass on the real module and catch at least 5 of 6 buggy versions."""
import os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).parent
WORK = Path.cwd()
REQUIRED_KILLS = 5


def run_tests(directory):
    return subprocess.run([sys.executable, "-m", "unittest", "test_textutils"],
                          cwd=directory, capture_output=True, text=True, timeout=30)


class Check(unittest.TestCase):
    def test_tests_exist_and_pass_on_real_module(self):
        self.assertTrue((WORK / "test_textutils.py").exists(), "test_textutils.py missing")
        self.assertEqual((WORK / "textutils.py").read_text(), (HERE / "project" / "textutils.py").read_text(),
                         "textutils.py was modified")
        r = run_tests(WORK)
        self.assertEqual(r.returncode, 0, r.stderr[-400:])

    def test_tests_catch_bugs(self):
        killed = []
        for mutant in sorted((HERE / "mutants").glob("m*.py")):
            with tempfile.TemporaryDirectory() as tmp:
                shutil.copy(WORK / "test_textutils.py", tmp)
                shutil.copy(mutant, Path(tmp) / "textutils.py")
                if run_tests(tmp).returncode != 0:
                    killed.append(mutant.stem)
        self.assertGreaterEqual(len(killed), REQUIRED_KILLS, f"only caught {killed}")


unittest.main()
