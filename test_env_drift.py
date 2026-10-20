import unittest
import os
import tempfile
from env_drift_sentinel import parse_env_file, audit, check_secrets

class TestEnvDriftSentinel(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_parse_env_file(self):
        path = os.path.join(self.test_dir.name, ".env.test")
        with open(path, "w") as f:
            f.write("# Comment\nKEY1=value1\nKEY2=\"quoted_value\"\n")
        keys = parse_env_file(path)
        self.assertEqual(keys["KEY1"], ("value1", 2))
        self.assertEqual(keys["KEY2"], ("quoted_value", 3))

    def test_check_secrets(self):
        leaks = check_secrets("API_KEY", "sk-1234567890abcdef1234567890abcdef")
        self.assertTrue(len(leaks) > 0)

    def test_audit(self):
        ex_path = os.path.join(self.test_dir.name, ".env.example")
        tar_path = os.path.join(self.test_dir.name, ".env")

        with open(ex_path, "w") as f:
            f.write("PORT=8080\nDATABASE_URL=\n")

        with open(tar_path, "w") as f:
            f.write("PORT=3000\nEXTRA_KEY=foo\n")

        report = audit(ex_path, tar_path)
        self.assertIn("DATABASE_URL", report["missing_in_target"])
        self.assertIn("EXTRA_KEY", report["extra_in_target"])

if __name__ == "__main__":
    unittest.main()
