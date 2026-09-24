#!/usr/bin/env python3
"""Fault row 19 (build plan V3, section 6b), fathom-meeting-agent: the files Claude reads and acts
on must not tell it to type a command a Mac does not have.

Before the fix, `.claude/agents/fathom-meeting-triage.md` line 33 said `pip install playwright`
and line 34 a bare `playwright install chromium`. A Mac has no `pip` (only `pip3`), and for a
standard (not admin) Mac user pip puts the `playwright` command in a folder Terminal does not
search (wave 0b reader finding).

What passes, for every instruction file (`.claude/**/*.md`, `CLAUDE.md`, `_CLAUDE.md`):
  1. `check_no_windows.py --kind instruction` from the test repo's harness finds nothing. That
     is the section 8f rule set, with its 1 instruction-file allowance: a Windows command inside
     "(on Windows: `...`)" on the same line.
  2. No line starts a bare `playwright install` (outside that bracket).
  3. Windows is not left without a command: every line naming a `python3 -m ...` command also
     carries "(on Windows: `python -m ...`)", so Claude on Windows still types `python`.

Run from the repo under test:   python3 _regress/test_instruction_files.py
It needs the test repo checked out beside it (../_mactest). Exit 0 = pass, 1 = fail.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path.cwd()
sys.path.insert(0, str(ROOT.parent / "_mactest" / "harness"))
import check_no_windows as CNW  # noqa: E402

BARE_PLAYWRIGHT = re.compile(r"(?:^|&&|;|\||`)\s*playwright\s+install\b")
PY3_CMD = re.compile(r"`python3 -m ([^`]+)`")


def instruction_files():
    files = sorted((ROOT / ".claude").rglob("*.md")) if (ROOT / ".claude").is_dir() else []
    for name in ("CLAUDE.md", "_CLAUDE.md"):
        if (ROOT / name).is_file():
            files.append(ROOT / name)
    return files


def main():
    files = instruction_files()
    if not files:
        print("FAIL: no instruction files found")
        return 1
    hits = []
    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for h in CNW.scan_line(line, "instruction"):
                hits.append((rel, n, h, line.strip()))
            rest = CNW.BRACKETED_WINDOWS.sub("", line)
            if BARE_PLAYWRIGHT.search(rest):
                hits.append((rel, n, "bare `playwright install`", line.strip()))
            for m in PY3_CMD.finditer(line):
                want = "(on Windows: `python -m %s`)" % m.group(1)
                if want not in line:
                    hits.append((rel, n, "no Windows form " + want, line.strip()))
    for rel, n, h, line in hits:
        print("%s line %d: %s | %s" % (rel, n, h, line[:160]))
    print("%d instruction file(s), %d hit(s) -> %s" % (len(files), len(hits), "FAIL" if hits else "PASS"))
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
