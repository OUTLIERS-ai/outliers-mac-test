"""Wave 0a, measurement M8: a strict run never makes a private Python folder (venv) that no
printed step made, and never tries a stand-in command.

Runs on Apple's own /usr/bin/python3 with nothing installed:
    /usr/bin/python3 -m unittest harness/tests/test_strict_no_venv.py -v

The shell is replaced by a stand-in that answers the way Homebrew's Python does on the test
Macs: `pip install` is refused with "externally-managed-environment" unless a venv is active.
Test 3 runs the same scene with strict mode off and expects the harness to make a venv, which
proves the stand-in really reaches the venv code (so a green strict result is not an empty one).

Proved red on purpose by the workflow: each block marked STRICT-RULE-A or STRICT-RULE-B in
mactest.py is removed in turn, and this file must then fail.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

HARNESS = Path(os.environ.get("MACTEST_DIR", str(Path(__file__).resolve().parents[1])))
sys.path.insert(0, str(HARNESS))
import mactest  # noqa: E402

REFUSED = ("error: externally-managed-environment\n\n"
           "x This environment is externally managed\n")


class Shell(object):
    """Stand-in for mactest.run_shell. Records every command line it is given."""

    def __init__(self):
        self.calls = []

    def __call__(self, cmd, cwd, stdin="", timeout=600, env_extra=None):
        self.calls.append(cmd)
        if " -m venv " in cmd:
            return 0, "", 0.1
        if "pip install" in cmd or "pip3 install" in cmd:
            if mactest.STATE["venv"] and not mactest.STATE.get("as_printed"):
                return 0, "Successfully installed requests", 0.1
            return 1, REFUSED, 0.1
        return 0, "", 0.1


def fresh_state():
    mactest.STATE.update({"venv": None, "bg": [], "plists_before": set(), "plists": [],
                          "shots": [], "as_printed": False})


class StrictRun(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.ctx = {"repo": "probe", "mac": "test", "out": Path(self.tmp), "repo_dir": Path(self.tmp)}
        self.shell = Shell()
        self.saved = (mactest.run_shell, mactest.STRICT)
        mactest.run_shell = self.shell
        fresh_state()

    def tearDown(self):
        mactest.run_shell, mactest.STRICT = self.saved
        fresh_state()

    def step(self):
        return {"id": "pip", "cmd": "pip install requests", "cwd": self.tmp}

    def test_1_strict_step_fails_and_makes_no_venv(self):
        mactest.STRICT = True
        attempts, verdict, sub = mactest.do_member_step(self.step(), self.ctx)
        self.assertEqual(verdict, "FAILS")
        self.assertEqual(sub, "")
        self.assertIsNone(mactest.STATE["venv"], "a strict run made a private Python folder")
        self.assertFalse([c for c in self.shell.calls if "-m venv" in c],
                         "a strict run ran python3 -m venv: %r" % self.shell.calls)
        self.assertEqual([a["label"] for a in attempts], ["as printed"],
                         "a strict run tried a stand-in command")

    def test_2_strict_make_venv_refuses_and_runs_nothing(self):
        mactest.STRICT = True
        notes = []
        self.assertFalse(mactest.make_venv(notes))
        self.assertEqual(self.shell.calls, [])
        self.assertIsNone(mactest.STATE["venv"])
        self.assertTrue(any("strict" in n for n in notes))

    def test_3_control_without_strict_the_same_scene_makes_a_venv(self):
        mactest.STRICT = False
        attempts, verdict, sub = mactest.do_member_step(self.step(), self.ctx)
        self.assertEqual(verdict, "WORKS-WITH-SUBSTITUTE")
        self.assertIsNotNone(mactest.STATE["venv"])
        self.assertTrue([c for c in self.shell.calls if "-m venv" in c])


if __name__ == "__main__":
    unittest.main(verbosity=2)
