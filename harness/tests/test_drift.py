"""The weekly drift backstop's verdict (build plan V3, section 7f), each way it must go RED.

    python3 -m unittest -v harness/tests/test_drift.py
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import drift  # noqa: E402

STAMP = {"main_commit": "d5d6be50c14aee10792815f3c990ce7f8e31df2b",
         "files": [{"path": "install.py", "category": "same", "sha256": "aa"},
                   {"path": "README.md", "category": "changed", "sha256": "bb"},
                   {"path": "guide/L2 (Mac).pdf", "category": "left out of the fingerprint"}]}
HEAD = "d5d6be50c14aee10792815f3c990ce7f8e31df2b"


class Judge(unittest.TestCase):
    def test_green_when_commit_and_shared_files_match(self):
        self.assertEqual(drift.judge(STAMP, HEAD, {"install.py": "aa", "README.md": "zz"},
                                     {"install.py": "aa", "README.md": "bb"}), "green")

    def test_red_when_main_moved_on(self):
        self.assertTrue(drift.judge(STAMP, "1234567abc", {"install.py": "aa"}, {"install.py": "aa"}).startswith("RED"))

    def test_red_when_a_shared_file_differs_in_the_mac_repo(self):
        r = drift.judge(STAMP, HEAD, {"install.py": "aa"}, {"install.py": "ab"})
        self.assertIn("Mac repo", r)

    def test_red_when_a_shared_file_differs_in_the_windows_repo(self):
        r = drift.judge(STAMP, HEAD, {"install.py": "ab"}, {"install.py": "aa"})
        self.assertIn("Windows repo", r)

    def test_a_changed_member_file_is_not_drift(self):
        self.assertEqual(drift.judge(STAMP, HEAD, {"install.py": "aa", "README.md": "x"},
                                     {"install.py": "aa", "README.md": "y"}), "green")


if __name__ == "__main__":
    unittest.main()
