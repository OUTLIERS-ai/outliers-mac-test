# -*- coding: utf-8 -*-
"""Row 2 on a Mac: Part 4 puts the morning list on the Mac's own timetable, a LaunchAgent at
~/Library/LaunchAgents/ai.outliers.sb.morning.plist, never a crontab line (the old printed line
broke on the space in "Second Brain" and on `python`). launchd then really runs it: the job
writes the morning list and the morning log, and today.py says when the list was last written.
The printed removal lines take it away again.

    python3 test_mac_morning_job.py <part folder>

Runs only on a Mac with CI=true (a GitHub throwaway Mac): it uses the machine's real home folder,
because launchd starts the job with the real home. Elsewhere it says SKIPPED, exit 3.
"""
import os
import plistlib
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sb"))
import sblib as T  # noqa: E402

if not (T.IS_MAC and T.ON_CI):
    print("SKIPPED: needs a throwaway Mac (macOS with CI=true), because it hands a job to launchd.")
    sys.exit(3)

part = T.part_dir()
py = sys.executable
home = Path.home()
label = "ai.outliers.sb.morning"
plist = home / "Library" / "LaunchAgents" / (label + ".plist")
log = home / ".outliers-sb-morning.log"
uid = os.getuid()

# A clean start: no second brain, no earlier job, no log.
subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
for p in (plist, log, home / ".outliers-sb"):
    if p.exists():
        p.unlink()
shutil.rmtree(str(home / "Second Brain"), ignore_errors=True)
vault = T.make_vault(home / "Second Brain", 3, pointer_home=home)

code, out = T.run([py, "install.py"], part, home, stdin="07:00\n\n\n\n")
install_out = out
T.check(code == 0, "Part 4 installs, Enter for every question", "exit %d" % code)
T.check("crontab" not in out, "no crontab line is printed")
T.check(not T.windows_hits(out), "nothing printed is a Windows command or word", T.windows_hits(out))
T.check(plist.exists(), "a LaunchAgent is written at ~/Library/LaunchAgents/%s.plist" % label)
if not plist.exists():
    T.done()

data = plistlib.loads(plist.read_bytes())
args = data.get("ProgramArguments", [])
T.check(data.get("Label") == label, "its label is %s" % label, data.get("Label"))
T.check(len(args) == 2 and Path(args[0]).exists() and os.access(args[0], os.X_OK),
        "it runs the Python the member installed with", args)
T.check(len(args) == 2 and args[1].endswith("/morning_job.py") and Path(args[1]).exists()
        and str(vault) not in args[1], "it runs the morning job from outside the second brain", args)
T.check(data.get("StartCalendarInterval") == {"Hour": 7, "Minute": 0}, "it runs at 07:00 each day",
        data.get("StartCalendarInterval"))
T.check(data.get("WorkingDirectory") == str(home), "it starts in the home folder, not the second brain",
        data.get("WorkingDirectory"))
lint = subprocess.run(["plutil", "-lint", str(plist)], capture_output=True, text=True)
T.check(lint.returncode == 0, "plutil says the file is valid", lint.stdout + lint.stderr)
listed = subprocess.run(["launchctl", "list", label], capture_output=True, text=True)
T.check(listed.returncode == 0, "launchd has it loaded now, not only after the next log-in", listed.stderr)

# Make launchd run it now, as it would at 07:00.
subprocess.run(["launchctl", "kickstart", "-k", "gui/%d/%s" % (uid, label)], capture_output=True)
seen = ""
for _ in range(30):
    time.sleep(2)
    seen = log.read_text(encoding="utf-8") if log.exists() else ""
    if "\twritten\t" in seen:
        break
T.check("\twritten\t" in seen, "launchd ran the job and it wrote the morning log", seen or "no log")
T.check((vault / "_engine" / "reports" / "today.txt").exists(), "the list is at _engine/reports/today.txt")
code, out = T.run(["python3", "_engine/today.py"], vault, home)
T.check("Morning list last written:" in out and "never" not in out, "today.py says when the list was last written", out)
cfg = __import__("json").loads((vault / "_layers" / "config.json").read_text(encoding="utf-8"))
T.check(cfg.get("morning_list_on_timetable") is True, "the settings record that the list is on the timetable", cfg)

# Installing again and answering no leaves the entry, and says so.
code, again = T.run([py, "install.py"], part, home, stdin="07:00\n\n\nn\n")
T.check("it is still there" in again and plist.exists(), "answering no later says the entry is still there", again[-800:])

# The removal lines, exactly as printed.
removal = [ln.strip() for ln in install_out.splitlines()
           if ln.strip().startswith(("launchctl unload", "rm ~/Library/LaunchAgents"))]
T.check(len(removal) == 2, "it prints the 2 lines that take it off the timetable", removal)
for ln in removal:
    subprocess.run(ln, shell=True, cwd=str(home))
T.check(not plist.exists(), "the printed removal lines take the file away")
T.check(subprocess.run(["launchctl", "list", label], capture_output=True).returncode != 0,
        "and launchd no longer has it")
T.done()
