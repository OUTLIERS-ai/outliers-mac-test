# -*- coding: utf-8 -*-
"""Row 20, Part 4: a morning job refused its second brain says so, instead of failing in silence.

The job (_engine/morning_job.py) writes each run's result to ~/.outliers-sb-morning.log, a file in
the home folder, outside the second brain. When reading the second brain raises PermissionError
("Operation not permitted", what macOS gives a job refused the Documents folder), the log records
"refused", and today.py prints "macOS refused access to <folder>" on a Mac (on Windows: "The
computer refused access to <folder>"), plus the fix, and "Morning list last written: <date>".
A member who never used the timetable sees nothing new.

    python test_refusal_is_reported.py <part folder>

Uses a throwaway home and runs the job by hand, so it never touches a timetable.
"""
import os
import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sb"))
import sblib as T  # noqa: E402

part = T.part_dir()
py = sys.executable

# Runs a program with os.listdir refusing one folder the way macOS refuses a job: EPERM.
REFUSE = "\n".join([
    "import os, runpy, sys",
    "real = os.listdir",
    "target = os.path.normcase(os.path.abspath(sys.argv[1]))",
    "def refuse(p='.'):",
    "    if os.path.normcase(os.path.abspath(str(p))).startswith(target):",
    "        raise PermissionError(1, 'Operation not permitted', str(p))",
    "    return real(p)",
    "os.listdir = refuse",
    "sys.argv = sys.argv[2:]",
    "runpy.run_path(sys.argv[0], run_name='__main__')",
])


def add(log, fields):
    with open(str(log), "a", encoding="utf-8", newline="\n") as fh:
        fh.write("\t".join(fields) + "\n")


home = T.throwaway_home("sb04-refused")
vault = T.make_vault(home / "Documents" / "Second Brain", 3, pointer_home=home)
log = home / ".outliers-sb-morning.log"
T.run([py, "install.py", "--no-schedule"], part, home, stdin="\n\n\n")
job = vault / "_engine" / "morning_job.py"
T.check(job.exists(), "Part 4 installs the morning job, _engine/morning_job.py")

# 0. No timetable and no log (a member who never used the timetable): nothing new is printed.
code, out = T.run([py, "_engine/today.py"], vault, home)
T.check(job.exists() and "Morning list" not in out and "refused" not in out,
        "with no timetable and no log, today.py prints nothing about the morning job", out)

# 1. A normal run.
code, out = T.run([py, str(job)], home, home)
text = log.read_text(encoding="utf-8") if log.exists() else ""
T.check(code == 0 and "\twritten\t" in text, "a normal run writes 'written' to the morning log", text or out)
T.check((vault / "_engine" / "reports" / "today.txt").exists(), "and the list to _engine/reports/today.txt")
code, out = T.run([py, "_engine/today.py"], vault, home)
T.check("Morning list last written:" in out and "never" not in out, "today.py says when the list was last written", out)

# 2. The same run, refused the second brain.
code, out = T.run([py, "-c", REFUSE, str(vault), str(job)], home, home)
last = log.read_text(encoding="utf-8").splitlines()[-1] if log.exists() else ""
T.check(code != 0 and "\trefused\t" in last and str(vault) in last and "Operation not permitted" in last,
        "a refused run writes 'refused', the folder and the reason to the morning log", last or out)
code, out = T.run([py, "_engine/today.py"], vault, home)
if T.IS_MAC:
    T.check("macOS refused access to %s" % vault in out, "today.py says macOS refused access to the folder", out)
    T.check("so it becomes %s" % (home / "Second Brain") in out, "and gives the fix: move it to ~/Second Brain", out)
    T.check(not T.windows_hits(out), "nothing printed is a Windows command or word", T.windows_hits(out))
else:
    T.check("The computer refused access to %s" % vault in out, "today.py says the computer refused access to the folder", out)
T.check("Morning list last written:" in out, "and still says when the list was last written", out)

# 2b. A failure comes with what to do; a refusal of a folder this second brain has since left
#     (it was moved) is old news and is not shown.
if job.exists():
    add(log, ["2026-09-24T07:05", "failed", str(vault), "ModuleNotFoundError: No module named x"])
code, out = T.run([py, "_engine/today.py"], vault, home)
T.check("The morning job failed on Thursday 24 September 2026, 07:05. Start your AI in your second brain" in out,
        "a failed run is reported with what to do", out)
if job.exists():
    add(log, ["2026-09-24T07:10", "refused", str(home / "Old" / "Place"), "[Errno 1] Operation not permitted"])
code, out = T.run([py, "_engine/today.py"], vault, home)
T.check(job.exists() and "refused access" not in out,
        "a refusal of a folder this second brain is no longer in is not shown", out)

# 3. On a Mac, a real refusal from the file system, not an injected one. The job file itself is
#    inside the refused folder, so a copy is run from outside it, as the Mac timetable does
#    (~/Library/Application Support/Outliers Second Brain/morning_job.py).
source = part / "sb" / "morning_job.py"
if T.IS_MAC and os.geteuid() != 0 and source.exists():
    outside = home / "Library" / "Application Support" / "Outliers Second Brain"
    outside.mkdir(parents=True, exist_ok=True)
    (outside / "morning_job.py").write_bytes(source.read_bytes())
    engine = vault / "_engine"
    mode = engine.stat().st_mode
    os.chmod(str(engine), 0)
    try:
        code, out = T.run([py, str(outside / "morning_job.py")], home, home)
    finally:
        os.chmod(str(engine), stat.S_IMODE(mode))
    last = log.read_text(encoding="utf-8").splitlines()[-1]
    T.check("\trefused\t" in last, "a folder the file system really refuses is logged as 'refused'", last)

T.cleanup(home)
T.done()
