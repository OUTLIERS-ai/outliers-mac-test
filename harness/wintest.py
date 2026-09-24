#!/usr/bin/env python3
"""Runs 1 Outliers member repo on GitHub's Windows machine, the way a Windows member would.

Build plan V3, section 9d: a fix made for the Mac must not break Windows. Every step a member
types is run EXACTLY as the repo prints it, in PowerShell (the terminal the Windows guides name),
with no stand-in command. The harness's own checks and the earlier parts installed first are
bash lines written for the Mac harness; they run in Git Bash with `python3` read as `python`,
because GitHub's Windows machine, like a member's, has no `python3` command.

Usage:  python harness/wintest.py <repo-name> <out-dir>

Steps of the kinds only a Mac has (login jobs, served pages, sign-in windows) are recorded as
NOT-TESTABLE here with that reason, never silently skipped.
"""
import datetime
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import specs  # noqa: E402

HOME = Path.home()
BASH = r"C:\Program Files\Git\bin\bash.exe"
TAIL = 4000


def now():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def expand(path, repo):
    if path is None:
        return str(HOME / repo)
    return os.path.expanduser(path.replace("{repo}", str(HOME / repo)))


def harness_line(cmd):
    """A bash line the harness wrote for the Mac, made to run on Windows: python3 -> python."""
    return re.sub(r"(?<![\w/.\-])python3(?![\w.\-])", "python", cmd)


def run(argv, cwd, stdin="", timeout=900):
    t0 = time.time()
    os.makedirs(cwd, exist_ok=True)
    try:
        p = subprocess.run(argv, cwd=cwd, input=stdin, capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace")
        code, out = p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired as e:
        code, out = "timeout", str(e.stdout or "") + "\n[wintest] stopped after %ss" % timeout
    return code, out, round(time.time() - t0, 1)


def powershell(cmd, cwd, stdin=""):
    return run(["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd], cwd, stdin)


def bash(cmd, cwd, stdin=""):
    return run([BASH, "-lc", cmd], cwd, stdin)


def looks_failed(code, out, step):
    ok = step.get("ok", [0])
    if ok != "any" and code not in ok:
        return True
    if "Traceback (most recent call last)" in out and not step.get("traceback_ok"):
        return True
    if step.get("expect") and not re.search(step["expect"], out, re.S | re.M):
        return True
    return False


def run_step(step, repo):
    kind = step.get("kind", "run")
    rec = {"id": step["id"], "kind": kind, "command_as_printed": step.get("cmd"),
           "counts": step.get("counts", kind != "prereq"), "started": now()}
    if step.get("not_testable"):
        rec.update(verdict="NOT-TESTABLE", reason=step["not_testable"])
        return rec
    if kind in ("launchd", "serve", "interactive", "shot"):
        rec.update(verdict="NOT-TESTABLE", reason="a Mac-only step kind in this harness (%s)" % kind)
        return rec
    cwd = expand(step.get("cwd"), repo)
    if kind in ("prereq", "check"):
        cmd = harness_line(step["cmd"])
        code, out, secs = bash(cmd, cwd, step.get("stdin", "\n" * 60))
        label = "harness line in Git Bash"
    else:
        cmd = step["cmd"]
        code, out, secs = powershell(cmd, cwd, step.get("stdin", "\n" * 60))
        label = "as printed, in PowerShell"
    failed = looks_failed(code, out, step)
    check_note = ""
    if not failed and step.get("check"):
        c2, o2, _ = bash(harness_line(step["check"]), expand(step.get("check_cwd", step.get("cwd")), repo))
        check_note = "check -> exit %s\n%s" % (c2, o2[-1500:])
        failed = c2 != 0
    rec.update(verdict="FAILS" if failed else "WORKS",
               attempts=[{"label": label, "command": cmd, "exit": code, "seconds": secs,
                          "output_tail": out[-TAIL:], "check": check_note}])
    return rec


def main():
    repo, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    os.environ["OUT"] = str(out)
    # WINTEST_FIX_PATCH (optional): a fix not yet on GitHub, from fixes/<name>/fix.patch, applied
    # to the member repo straight after it is cloned, so the Windows walk-through tests the fix
    # (plan 9d) before it is pushed. Recorded as its own step, never counted.
    patch = os.environ.get("WINTEST_FIX_PATCH", "").strip()
    steps = []
    for s in specs.get(repo)["steps"]:
        steps.append(run_step(s, repo))
        if patch and s["id"] == "clone" and steps[-1]["verdict"] == "WORKS":
            code, out, secs = run(["git", "apply", "--verbose", str(Path(patch).resolve())],
                                  str(HOME / repo))
            steps.append({"id": "apply-fix-patch", "kind": "prereq", "counts": False,
                          "verdict": "WORKS" if code == 0 else "FAILS", "started": now(),
                          "attempts": [{"label": "harness", "command": "git apply " + patch,
                                        "exit": code, "seconds": secs,
                                        "output_tail": out[-TAIL:]}]})
            if code != 0:
                print("the fix patch did not apply: %s" % out[-800:], flush=True)
                return 1
    for s in steps:
        print("[%s] %s" % (s["verdict"], s["id"]), flush=True)
    counted = [s for s in steps if s["counts"]]
    fails = [s["id"] for s in counted if s["verdict"] == "FAILS"]
    report = {"meta": {"repo": repo, "machine": "windows-latest", "finished": now(),
                       "python": run(["python", "--version"], str(HOME))[1].strip()},
              "verdict": "FAILS" if fails else "WORKS", "failed_steps": fails, "steps": steps}
    (out / ("%s--windows.json" % repo)).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("REPO VERDICT: %s" % report["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
