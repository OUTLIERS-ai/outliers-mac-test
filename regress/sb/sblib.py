# -*- coding: utf-8 -*-
"""Shared helpers for the Second Brain fix tests (build plan V3, rows 2, 18, 19, 20 and 23).

For future Claude: the tests in regress/sb-0N/ run against a downloaded member repo (a part repo,
or 1 part folder inside outliers-second-brain), never against Ashley's PC settings. Each test is a
plain script: exit 0 = pass, 1 = fail, and every check prints PASS or FAIL with what it saw.

Home folders: a throwaway home is made under the system's temp folder unless the test says it
needs the machine's real home (only the tests that hand a job to launchd or the Windows task
scheduler, and those run only on GitHub's throwaway machines, where CI=true).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[2] / "harness"
sys.path.insert(0, str(HARNESS))
import check_no_windows as CNW  # noqa: E402

IS_MAC = sys.platform == "darwin"
IS_WIN = os.name == "nt"
ON_CI = os.environ.get("CI", "").lower() == "true"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
FAILS = []


def check(ok, what, seen=""):
    print("%s  %s%s" % ("PASS" if ok else "FAIL", what, ("\n      saw: %s" % seen) if (seen and not ok) else ""))
    if not ok:
        FAILS.append(what)
    return ok


def done():
    print("")
    print("RESULT: %s" % ("all checks passed" if not FAILS else "%d check(s) failed" % len(FAILS)))
    sys.exit(1 if FAILS else 0)


def part_dir():
    """The part folder under test: argv[1], or the current folder."""
    return Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()


def throwaway_home(name):
    # resolve(): on a Mac the temp folder is reached through a link (/var is /private/var), and
    # Part 1 records the resolved address; comparing against the unresolved one would fail.
    home = Path(tempfile.mkdtemp(prefix="sbtest-%s-" % name)).resolve()
    (home / "Documents").mkdir()
    return home


def env_for(home):
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), PYTHONIOENCODING="utf-8",
               PYTHONDONTWRITEBYTECODE="1")
    return env


def run(argv, cwd, home, stdin="\n" * 20, timeout=300):
    p = subprocess.run(argv, cwd=str(cwd), input=stdin, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env_for(home),
                       creationflags=NO_WINDOW, timeout=timeout)
    out = p.stdout + ("\n" + p.stderr if p.stderr.strip() else "")
    print("---- %s (in %s), exit %d" % (" ".join(Path(a).name if i == 0 else a for i, a in enumerate(argv)),
                                         cwd, p.returncode))
    print(out.rstrip())
    print("---- end")
    return p.returncode, out


def make_vault(where, layer, pointer_home=None):
    """A second brain as far as the installers can tell: _layers/config.json at a layer."""
    (where / "_layers").mkdir(parents=True, exist_ok=True)
    (where / "_layers" / "config.json").write_text(
        json.dumps({"series": "outliers-second-brain", "layer": layer}), encoding="utf-8")
    for room in ("Areas", "Resources", "Archive"):
        (where / room).mkdir(exist_ok=True)
    if pointer_home is not None:
        (pointer_home / ".outliers-sb").write_text(str(where), encoding="utf-8")
    return where


def windows_hits(text):
    """Lines of printed output a Mac member must never see (plan 8f rules)."""
    return CNW.scan_text(text, "output")


def cleanup(home):
    shutil.rmtree(str(home), ignore_errors=True)
