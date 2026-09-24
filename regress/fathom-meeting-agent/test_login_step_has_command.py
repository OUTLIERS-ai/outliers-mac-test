#!/usr/bin/env python3
"""Fault row 22 (build plan V3, section 6b), fathom-meeting-agent: the README's Step 3 ("log into
Fathom yourself, by hand, once") must give the command that opens Playwright's browser, and the
agent must use the same browser profile the member logged into.

Before the fix, Step 3 said "Open the browser Playwright just installed" and printed nothing to
type, on any system; the strict run had no command to run.

What passes:
  1. README Step 3 has a code block with a `python -m playwright open` line (or `python3 -m`)
     that names a profile folder with `--user-data-dir=<folder>` and Fathom's address.
  2. The agent file `.claude/agents/fathom-meeting-triage.md` names that same folder, so the
     agent opens the browser the member is logged into and not a fresh one.
  3. `.gitignore` keeps that folder out of git: it holds the member's Fathom login.
  4. On a GitHub test machine only (GITHUB_ACTIONS set): in a private Python folder with
     Playwright installed, `playwright open --help` lists every option the line uses, and the
     line itself, run with Fathom's address swapped for about:blank, opens the browser and
     creates the profile folder. The browser is closed 3 seconds after the folder appears (at
     most 25 seconds). Fathom is never contacted and nothing is logged into.

Run from the repo under test:   python3 _regress/test_login_step_has_command.py
Exit 0 = pass, 1 = fail.
"""
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path.cwd()
NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)
OPEN_LINE = re.compile(r"^\s*(?:python3?|py)\s+-m\s+playwright\s+open\b(.*)$")


def step3(readme):
    m = re.search(r"\*\*Step 3\b(.*?)(?=\*\*Step 4\b|\n## )", readme, re.S)
    return m.group(1) if m else ""


def code_lines(text):
    out, inside = [], False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            inside = not inside
            continue
        if inside:
            out.append(line)
    return out


def fail(msg):
    print("FAIL: " + msg)
    return 1


def main():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    s3 = step3(readme)
    if not s3:
        return fail("README.md has no Step 3 section")
    lines = [l for l in code_lines(s3) if OPEN_LINE.match(l)]
    if not lines:
        print("README Step 3, as printed:\n" + s3.strip()[:800])
        return fail("README Step 3 prints no command that opens Playwright's browser")
    line = lines[0].strip()
    print("README Step 3 command: " + line)
    args = shlex.split(OPEN_LINE.match(line).group(1))
    prof = next((a.split("=", 1)[1] for a in args if a.startswith("--user-data-dir=")), None)
    if not prof:
        return fail("the command names no --user-data-dir=<folder>, so the login is not kept")
    if not any("fathom.video" in a for a in args):
        return fail("the command does not open Fathom's address")
    agent = (ROOT / ".claude" / "agents" / "fathom-meeting-triage.md").read_text(encoding="utf-8")
    if prof not in agent:
        return fail("the agent file never names the profile folder %r, so it would open a browser "
                    "with no login" % prof)
    ignore = [l.strip().rstrip("/") for l in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()]
    if prof.rstrip("/") not in ignore and ("/" + prof.rstrip("/")) not in ignore:
        return fail(".gitignore does not keep %r (the member's Fathom login) out of git" % prof)
    print("static checks: PASS (profile folder %r named in README, agent file and .gitignore)" % prof)

    if not os.environ.get("GITHUB_ACTIONS"):
        print("not a GitHub test machine: the browser is not opened here (it would open a window)")
        return 0
    return run_on_test_machine(args, prof)


def stop_tree(p):
    """Stop the command and every process it started (the Playwright driver and the browser)."""
    if p.poll() is None:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True,
                           creationflags=NOWIN)
        else:
            import signal
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()


def run_on_test_machine(args, prof):
    venv = Path(tempfile.mkdtemp(prefix="fathom-row22-")) / "v"
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    py = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run([str(py), "-m", "pip", "install", "-q", "playwright"], check=True)
    subprocess.run([str(py), "-m", "playwright", "install", "chromium"], check=True)
    helptext = subprocess.run([str(py), "-m", "playwright", "open", "--help"], capture_output=True,
                              text=True, check=True).stdout
    for a in args:
        if a.startswith("--"):
            opt = a.split("=", 1)[0]
            if opt not in helptext:
                return fail("playwright open does not accept %s" % opt)
    work = Path(tempfile.mkdtemp(prefix="fathom-row22-run-"))
    run_args = ["about:blank" if "fathom.video" in a else a for a in args]
    # Output goes to a file, not a pipe: the browser the command starts would hold a pipe open
    # after its parent is stopped, and reading it would never end. The whole process tree is
    # stopped at the end (its own session on a Mac, taskkill /T on Windows).
    log = work.parent / (work.name + "-open.log")
    with open(log, "w", encoding="utf-8") as lf:
        if os.name == "nt":
            p = subprocess.Popen([str(py), "-m", "playwright", "open"] + run_args, cwd=str(work),
                                 stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        else:
            p = subprocess.Popen([str(py), "-m", "playwright", "open"] + run_args, cwd=str(work),
                                 stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                 start_new_session=True)
        made = False
        for _ in range(50):
            time.sleep(0.5)
            if (work / prof).is_dir() and any((work / prof).iterdir()):
                made = True
                time.sleep(3)
                break
            if p.poll() is not None:
                break
        stop_tree(p)
    out = log.read_text(encoding="utf-8", errors="replace")
    print("playwright open output (last 800 chars):\n" + out[-800:])
    if not made:
        return fail("running the line did not create the profile folder %r" % prof)
    print("the line opened the browser and created %r: PASS" % prof)
    shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
