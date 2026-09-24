# -*- coding: utf-8 -*-
"""Runs several Second Brain fix tests as 1 check, for fixes/<name>/check.txt.

    python run.py <test.py>@<part folder> [...]
    python run.py --list <file>      # the same, 1 per line (what a fix's test.patch adds)

A test that exits 3 said SKIPPED (it is for another system); it is listed as skipped, never as
passed. Exit 0 only when at least 1 test ran and every test that ran passed; 1 when any failed;
3 when none ran here at all (so a check with nothing to run on this machine can never go green).
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
ran, failed, skipped = [], [], []
args = sys.argv[1:]
if args[:1] == ["--list"]:
    listed = Path(args[1])
    if not listed.exists():
        print("No test list at %s: nothing to run, so this cannot pass." % listed)
        sys.exit(1)
    args = [ln.strip() for ln in listed.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.startswith("#")]
for arg in args:
    test, _, part = arg.partition("@")
    code = subprocess.run([sys.executable, "-B", str(HERE / test), part or "."]).returncode
    (skipped if code == 3 else failed if code != 0 else ran).append(test)
    if code not in (0, 3):
        ran.append(test)
print("")
print("SUMMARY: %d ran, %d failed, %d skipped on this machine" % (len(ran), len(failed), len(skipped)))
for t in failed:
    print("  failed:  %s" % t)
for t in skipped:
    print("  skipped: %s (for another system; not counted as passed)" % t)
sys.exit(1 if failed else 3 if not ran else 0)
