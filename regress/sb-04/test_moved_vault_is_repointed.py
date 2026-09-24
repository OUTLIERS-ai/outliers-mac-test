# -*- coding: utf-8 -*-
"""Rows 20 and 23 on a Mac: the fix today.py prints after a refusal is "move the folder to
~/Second Brain, then install Part 4 again". This proves the second half: Part 4 finds the moved
folder, records its new address in ~/.outliers-sb, and changes only the address line inside the
second-brain section of ~/.claude/CLAUDE.md; everything else in that file stays byte-identical.

    python3 test_moved_vault_is_repointed.py <part folder>     # on a Mac; elsewhere SKIPPED, exit 3
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sb"))
import sblib as T  # noqa: E402

if not T.IS_MAC:
    print("SKIPPED: this test is for a Mac only. On Windows Part 4 never rewrites the recorded "
          "address, which the Windows walk-through proves.")
    sys.exit(3)

part = T.part_dir()
py = sys.executable
home = T.throwaway_home("sb04-moved")
old = T.make_vault(home / "Documents" / "Second Brain", 3, pointer_home=home)
(home / ".claude").mkdir()
before = ("# My own notes for Claude\n\nKeep answers short.\n\n"
          "<!-- OUTLIERS-SECOND-BRAIN:BEGIN -->\n## My second brain\n"
          "My second brain is at: %s\n"
          "When I ask about my notes, people, projects, meetings or decisions, that folder is\n"
          "the source of truth. Read %s/CLAUDE.md before acting in it.\n"
          "<!-- OUTLIERS-SECOND-BRAIN:END -->\n\nA line after the section.\n" % (old, old))
manual = home / ".claude" / "CLAUDE.md"
manual.write_text(before, encoding="utf-8")

new = home / "Second Brain"
shutil.move(str(old), str(new))
code, out = T.run([py, "install.py", "--no-schedule"], part, home, stdin="\n\n\n")
T.check("Found your second brain: %s" % new in out, "Part 4 finds the moved folder at ~/Second Brain", out[:800])
T.check((home / ".outliers-sb").read_text(encoding="utf-8").strip() == str(new),
        "~/.outliers-sb now records ~/Second Brain")
after = manual.read_text(encoding="utf-8")
T.check(after == before.replace(str(old), str(new)),
        "~/.claude/CLAUDE.md names the new address, and nothing else in it changed", after)
T.check("changed the line in ~/.claude/CLAUDE.md" in out, "it says it changed that line", out[-800:])

# Run again: nothing more to change, nothing said.
code, out = T.run([py, "install.py", "--no-schedule"], part, home, stdin="\n\n\n")
T.check("new address" not in out, "a second run changes nothing and says nothing about an address", out[-800:])
T.cleanup(home)
T.done()
