# -*- coding: utf-8 -*-
"""Row 20, Part 2's check: once Part 4's morning job has a log (~/.outliers-sb-morning.log), the
check says when the morning list was last written, and says so plainly if the last run was
refused its folder or failed. With no log (Part 4 not installed) it prints nothing new. A refusal
of a folder this second brain has since left (it was moved) is old news and is not shown.

    python test_doctor_reports_morning_job.py <part folder>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sb"))
import sblib as T  # noqa: E402

part = T.part_dir()
py = sys.executable
home = T.throwaway_home("sb02-doctor")
vault = T.make_vault(home / "Documents" / "Second Brain", 1, pointer_home=home)
T.run([py, "install.py"], part, home)
T.check((vault / "_engine" / "doctor.py").exists(), "Part 2 installs the check")

code, out = T.run([py, "_engine/doctor.py"], vault, home)
T.check("Morning list" not in out, "with no morning log, the check prints nothing about it", out)

log = home / ".outliers-sb-morning.log"


def add(line):
    with open(str(log), "a", encoding="utf-8", newline="\n") as fh:
        fh.write(line + "\n")


add("\t".join(["2026-09-23T07:00", "written", str(vault), str(vault / "_engine" / "reports" / "today.txt")]))
add("\t".join(["2026-09-24T07:00", "refused", str(vault), "[Errno 1] Operation not permitted"]))
code, out = T.run([py, "_engine/doctor.py"], vault, home)
T.check("Morning list last written: Wednesday 23 September 2026, 07:00" in out,
        "the check says when the list was last written", out)
who = "macOS" if T.IS_MAC else "The computer"
T.check("%s refused access to %s" % (who, vault) in out,
        "the check says the last run was refused, and which folder", out)
if T.IS_MAC:
    T.check(not T.windows_hits(out), "nothing printed is a Windows command or word", T.windows_hits(out))

add("\t".join(["2026-09-24T07:05", "failed", str(vault), "ModuleNotFoundError: No module named x"]))
code, out = T.run([py, "_engine/doctor.py"], vault, home)
T.check("The morning job failed on Thursday 24 September 2026, 07:05" in out,
        "the check says the last run failed", out)

add("\t".join(["2026-09-24T07:10", "refused", str(home / "Old" / "Place"), "[Errno 1] Operation not permitted"]))
code, out = T.run([py, "_engine/doctor.py"], vault, home)
T.check("refused access" not in out,
        "a refusal of a folder this second brain is no longer in is not shown", out)
T.cleanup(home)
T.done()
