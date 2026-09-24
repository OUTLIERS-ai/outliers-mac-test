# -*- coding: utf-8 -*-
"""Row 2 with Ashley's decision 3 (2026-09-24): Part 4 ASKS before it puts the morning list on the
computer's timetable, on Windows and on a Mac. Answering no adds nothing; --no-schedule skips the
question and adds nothing; answering yes (GitHub's throwaway Windows machine only) adds the task,
the task runs the morning job with no window, the job writes the morning log, and the printed
removal line takes it away again.

    python test_morning_job_asks.py <part folder>

On Ashley's PC this never answers yes, and it refuses to answer at all to an installer that does
not ask first (the old installer would add a real task to his PC).
"""
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sb"))
import sblib as T  # noqa: E402

part = T.part_dir()
py = sys.executable
TASK = "OutliersSecondBrain-Morning"
QUESTION = "timetable"


def task_exists():
    if not T.IS_WIN:
        return False
    q = subprocess.run(["schtasks", "/Query", "/TN", TASK], capture_output=True, text=True,
                       creationflags=T.NO_WINDOW)
    return q.returncode == 0


def plist_in(home):
    return home / "Library" / "LaunchAgents" / "ai.outliers.sb.morning.plist"


def asked(out):
    return any(QUESTION in ln and "(Y/n)" in ln for ln in out.splitlines())


source = (part / "install.py").read_text(encoding="utf-8")
if T.IS_WIN and not T.ON_CI and "timetable, so it runs by itself" not in source:
    T.check(False, "the installer asks before adding a timetable (not run: on this PC the old "
                   "installer would add a real scheduled task, so it is only run on GitHub)")
    T.done()

# 1. Answer no.
home = T.throwaway_home("sb04-no")
T.make_vault(home / "Second Brain", 3, pointer_home=home)
before = task_exists()
code, out = T.run([py, "install.py"], part, home, stdin="\n\n\nn\n")
T.check(asked(out), "it asks before adding the morning list to the timetable", out[-1500:])
T.check(task_exists() == before, "answering no adds no scheduled task")
T.check(not plist_in(home).exists(), "answering no writes no LaunchAgent")
T.check("Nothing was put on a timetable" in out, "it says nothing was put on a timetable")
if T.IS_MAC:
    T.check(not T.windows_hits(out), "nothing printed is a Windows command or word", T.windows_hits(out))
T.cleanup(home)

# 2. --no-schedule: no question, nothing added.
home = T.throwaway_home("sb04-flag")
T.make_vault(home / "Second Brain", 3, pointer_home=home)
before = task_exists()
code, out = T.run([py, "install.py", "--no-schedule"], part, home, stdin="\n\n\n")
T.check(not asked(out), "with --no-schedule it does not ask")
T.check(task_exists() == before and not plist_in(home).exists(), "with --no-schedule nothing is added")
T.check("--no-schedule" in out, "it says it skipped the timetable because of --no-schedule")
T.cleanup(home)

# 3. Answer yes, on GitHub's throwaway Windows machine only (a real task, real home).
if T.IS_WIN and T.ON_CI:
    home = Path.home()
    vault = T.make_vault(home / "Documents" / "Second Brain", 3, pointer_home=home)
    log = home / ".outliers-sb-morning.log"
    if log.exists():
        log.unlink()
    code, out = T.run([py, "install.py"], part, home, stdin="\n\n\ny\n")
    T.check(asked(out) and task_exists(), "answering yes adds the scheduled task", out[-1500:])
    T.check("schtasks /Delete /TN %s /F" % TASK in out, "it prints how to take it off the timetable")
    subprocess.run(["schtasks", "/Run", "/TN", TASK], capture_output=True, creationflags=T.NO_WINDOW)
    seen = ""
    for _ in range(60):
        time.sleep(2)
        seen = log.read_text(encoding="utf-8") if log.exists() else ""
        if "\twritten\t" in seen:
            break
    T.check("\twritten\t" in seen, "the task ran the morning job, which wrote the morning log", seen or "no log")
    T.check((vault / "_engine" / "reports" / "today.txt").exists(), "the morning list was written to _engine/reports/today.txt")
    code, out = T.run([py, "_engine/today.py"], vault, home)
    T.check("Morning list last written:" in out and "never" not in out, "today.py says when the list was last written", out)
    subprocess.run("schtasks /Delete /TN %s /F" % TASK, shell=True, capture_output=True, creationflags=T.NO_WINDOW)
    T.check(not task_exists(), "the printed removal line takes the task away")
elif T.IS_WIN:
    print("NOT RUN here: answering yes adds a real scheduled task, so that part runs on GitHub only.")

T.done()
