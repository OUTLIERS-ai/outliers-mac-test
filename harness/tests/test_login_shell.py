"""Wave 0b: in a login-shell run (MACTEST_LOGIN=1) every step starts as a new Terminal window
does: a login shell whose environment has only HOME, USER, LOGNAME, SHELL and TERM (plus the
harness's own OUT and the step's settings), so PATH comes only from the Mac's own files and the
member's profile files (build plan V3, section 9a).

    /usr/bin/python3 -m unittest -v harness/tests/test_login_shell.py

Proved red on purpose by the workflow: the 2 lines marked LOGIN-RULE in mactest.py are removed
and this file must then fail.
"""
import os
import sys
import unittest
from pathlib import Path

HARNESS = Path(os.environ.get("MACTEST_DIR", str(Path(__file__).resolve().parents[1])))
sys.path.insert(0, str(HARNESS))
import mactest  # noqa: E402

SENTINEL = "/tmp/runner-only-folder-a-member-never-has"


class LoginShell(unittest.TestCase):
    def setUp(self):
        self.was = mactest.LOGIN
        mactest.LOGIN = True

    def tearDown(self):
        mactest.LOGIN = self.was

    def test_argv_is_a_login_shell(self):
        argv, env = mactest.shell_argv("echo hi")
        self.assertEqual(argv, ["/bin/zsh", "-l", "-i", "-c", "echo hi"])

    def test_environment_holds_only_the_new_window_names(self):
        os.environ["GITHUB_SOMETHING"] = "x"
        argv, env = mactest.shell_argv("true", {"CRM_DIR": "~/CRM"})
        allowed = {"HOME", "USER", "LOGNAME", "SHELL", "TERM", "OUT", "CRM_DIR"}
        self.assertTrue(set(env) <= allowed, sorted(set(env) - allowed))
        self.assertNotIn("PATH", env)
        self.assertEqual(env["CRM_DIR"], os.path.expanduser("~/CRM"))
        self.assertEqual(env["SHELL"], "/bin/zsh")

    @unittest.skipUnless(sys.platform == "darwin", "needs a Mac's zsh and /etc/paths")
    def test_a_folder_only_the_test_mac_has_is_not_on_the_step_path(self):
        old = os.environ.get("PATH", "")
        os.environ["PATH"] = SENTINEL + ":" + old
        try:
            code, out, _ = mactest.run_shell('echo "PATH=$PATH"', "/tmp", "", 60)
        finally:
            os.environ["PATH"] = old
        self.assertEqual(code, 0, out)
        line = [l for l in out.splitlines() if l.startswith("PATH=")][-1]
        self.assertNotIn(SENTINEL, line)
        self.assertIn("/usr/bin", line)


if __name__ == "__main__":
    unittest.main()
