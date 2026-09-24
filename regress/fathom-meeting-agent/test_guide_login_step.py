#!/usr/bin/env python3
"""Wave 1 leftover (review/wave1-singles.md, "Not fixed" 1), fathom-meeting-agent: the guide PDF's
source, `guide/build_guide.py`, must print in Step 4 ("log into Fathom yourself, by hand, once")
the same command that opens Playwright's browser as the README's Step 3.

Before the fix the README gave the command (fault row 22) but the guide said "Open the browser
Playwright just installed" with nothing to type, so a member reading the PDF had no command.

What passes: the Step 4 part of `guide/build_guide.py` contains, inside a `<div class="cmd">`,
the README's `python -m playwright open ...` line word for word, and the README's `cd` line.
No browser is opened.

Run from the repo under test:   python3 _regress/test_guide_login_step.py
Exit 0 = pass, 1 = fail.
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path.cwd()
OPEN_LINE = re.compile(r"^\s*(?:python3?|py)\s+-m\s+playwright\s+open\b.*$", re.M)


def main():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    s3 = re.search(r"\*\*Step 3\b(.*?)(?=\*\*Step 4\b|\n## )", readme, re.S)
    want = OPEN_LINE.search(s3.group(1)) if s3 else None
    if not want:
        print("FAIL: README Step 3 prints no command that opens Playwright's browser (fault row 22 first)")
        return 1
    want = want.group(0).strip()
    cd = re.search(r"^\s*cd\s+\S+\s*$", s3.group(1), re.M)
    src = (ROOT / "guide" / "build_guide.py").read_text(encoding="utf-8")
    s4 = re.search(r"Step 4 &nbsp;/&nbsp;(.*?)(?=Step 5 &nbsp;/&nbsp;)", src, re.S)
    if not s4:
        print("FAIL: guide/build_guide.py has no Step 4 section")
        return 1
    cmds = [html.unescape(re.sub(r"<br\s*/?>", "\n", c)) for c in
            re.findall(r'<div class="cmd">(.*?)</div>', s4.group(1), re.S)]
    lines = [l.strip() for c in cmds for l in c.splitlines()]
    print("README Step 3 command: %s" % want)
    print("guide Step 4 commands: %s" % (lines or "none"))
    if want not in lines:
        print("FAIL: the guide's Step 4 does not print the README's command")
        return 1
    if cd and cd.group(0).strip() not in lines:
        print("FAIL: the guide's Step 4 leaves out the README's %r" % cd.group(0).strip())
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
