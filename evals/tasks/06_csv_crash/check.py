import shutil, subprocess, sys, unittest
from pathlib import Path

HERE = Path(__file__).parent


class Check(unittest.TestCase):
    def test_prints_total_with_original_data(self):
        # Restore the original data so fixing the data file doesn't count.
        shutil.copy(HERE / "project" / "data.csv", "data.csv")
        r = subprocess.run([sys.executable, "report.py"], capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr[-400:])
        self.assertEqual(r.stdout.strip(), "Total revenue: 75.00")

    def test_other_file(self):
        Path("other.csv").write_text("product,price,qty\na,1.50,2\nb,3.00,1\n")
        import importlib, os
        sys.path.insert(0, os.getcwd())
        import report
        importlib.reload(report)
        self.assertEqual(round(report.total_revenue("other.csv"), 2), 6.0)


unittest.main()
