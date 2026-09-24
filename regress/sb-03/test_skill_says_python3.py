# -*- coding: utf-8 -*-
"""Row 19, Part 3: the YouTube assistant's instructions (youtube-to-notes/SKILL.md, and the Claude
Code assistant file Part 3 writes from it) tell Claude a command that works on a Mac. The file is
shared by both systems, so the Windows form is allowed only in the exact both-systems wording
"(on Windows: `...`)" (plan 7c rule 5). Checked with the same rules as check_no_windows.py.

    python test_skill_says_python3.py <part folder>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sb"))
import sblib as T  # noqa: E402

part = T.part_dir()
py = sys.executable


def hits(path):
    return T.CNW.scan_text(path.read_text(encoding="utf-8"), "instruction")


skill = part / "youtube-to-notes" / "SKILL.md"
h = hits(skill)
T.check(not h, "youtube-to-notes/SKILL.md tells Claude no Windows-only command", h)
text = skill.read_text(encoding="utf-8")
T.check('python3 "<this skill\'s folder>/scripts/youtube_words.py"' in text,
        "it says python3 for the helper", "")
T.check("(on Windows: `python \"<this skill's folder>/scripts/youtube_words.py\"" in text,
        "and gives the Windows form in the both-systems wording", "")

home = T.throwaway_home("sb03-skill")
vault = T.make_vault(home / "Documents" / "Second Brain", 2, pointer_home=home)
T.run([py, "install.py"], part, home)
for f in (vault / ".claude" / "agents" / "the-youtube-reader.md",
          vault / ".claude" / "skills" / "youtube-to-notes" / "SKILL.md",
          vault / ".agents" / "skills" / "youtube-to-notes" / "SKILL.md"):
    T.check(f.exists() and not hits(f), "installed %s tells Claude no Windows-only command"
            % f.relative_to(vault).as_posix(), hits(f) if f.exists() else "missing")
T.cleanup(home)
T.done()
