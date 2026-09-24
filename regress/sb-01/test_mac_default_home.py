# -*- coding: utf-8 -*-
"""Row 23, Part 1: on a Mac a NEW second brain goes to ~/Second Brain, not ~/Documents/Second Brain
(a job that starts by itself can be refused the Documents folder). One that already exists is never
moved: Part 1 run again offers the folder the Mac already has.

    python3 test_mac_default_home.py <part folder>      # on a Mac; elsewhere it says SKIPPED, exit 3
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sb"))
import sblib as T  # noqa: E402

if not T.IS_MAC:
    print("SKIPPED: this test is for a Mac only. Windows keeps ~/Documents/Second Brain, which the "
          "Windows walk-through proves.")
    sys.exit(3)

part = T.part_dir()
py = sys.executable

# 1. A new Mac: Enter for every question.
home = T.throwaway_home("sb01-new")
code, out = T.run([py, "install.py"], part, home)
new = home / "Second Brain"
T.check(code == 0, "a new install finishes", "exit %d" % code)
T.check("[%s]" % new in out, "the default offered is ~/Second Brain", out[:600])
T.check((new / "_layers" / "config.json").exists(), "the second brain is made at ~/Second Brain")
T.check(not (home / "Documents" / "Second Brain").exists(), "nothing is made in ~/Documents")
pointer = (home / ".outliers-sb").read_text(encoding="utf-8").strip() if (home / ".outliers-sb").exists() else ""
T.check(pointer == str(new), "Part 1 records ~/Second Brain as the address", pointer)
T.check(not T.windows_hits(out), "nothing printed is a Windows command or word", T.windows_hits(out))
T.cleanup(home)

# 2. A Mac that already has a second brain in Documents (installed before this fix), no record
#    of where: it is offered again, never a new one beside it.
home = T.throwaway_home("sb01-old")
old = T.make_vault(home / "Documents" / "Second Brain", 4)
code, out = T.run([py, "install.py"], part, home)
T.check("[%s]" % old in out, "an existing second brain in Documents is offered, not moved", out[:600])
T.check(not (home / "Second Brain").exists(), "no second second brain is made at ~/Second Brain")
T.cleanup(home)

# 3. A second brain somewhere else, recorded by Part 1 earlier: that address is offered.
home = T.throwaway_home("sb01-else")
elsewhere = T.make_vault(home / "Work" / "Brain", 2, pointer_home=home)
code, out = T.run([py, "install.py"], part, home)
T.check("[%s]" % elsewhere in out, "the recorded address is offered again", out[:600])
T.check(not (home / "Second Brain").exists(), "nothing new at ~/Second Brain")
T.cleanup(home)

T.done()
