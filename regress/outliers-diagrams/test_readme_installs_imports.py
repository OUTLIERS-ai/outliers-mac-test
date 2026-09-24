#!/usr/bin/env python3
"""Fault row 15 (build plan V3, section 6b), outliers-diagrams: the install line in README.md must
install every add-on the repo's programs import.

Before the fix the README installed Playwright only, and `labs/phone_width.py` stopped with
"No module named 'PIL'" (baseline run, both test Macs). It is not a Mac fault: any fresh machine
following the README fails the same way.

What is read: every `import x` and `from x import` line in every .py file of the repo. An add-on
is any top-level name that is neither part of Python itself (`sys.stdlib_module_names`) nor a
file or folder of the repo. Each must appear in a `pip install ...` line (any of the command
forms) inside a code block of README.md, under its install name (`PIL` installs as `pillow`).

Run from the repo under test:   python3 _regress/test_readme_installs_imports.py
Exit 0 = pass, 1 = fail.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path.cwd()
IMPORT = re.compile(r"^\s*(?:import|from)\s+([A-Za-z_][\w]*)")
PIP = re.compile(r"\bpip3?\s+install\s+(.+)$")
INSTALL_NAME = {"PIL": "pillow", "cv2": "opencv-python", "yaml": "pyyaml", "bs4": "beautifulsoup4",
                "fitz": "pymupdf", "sklearn": "scikit-learn"}


def readme_installs():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    names, inside = set(), False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            inside = not inside
            continue
        m = PIP.search(line) if inside else None
        if m:
            for w in m.group(1).split():
                if not w.startswith("-"):
                    names.add(re.split(r"[<>=\[]", w)[0].lower())
    return names


def repo_imports():
    local = {p.stem for p in ROOT.rglob("*.py")} | {p.name for p in ROOT.rglob("*") if p.is_dir()}
    found = {}
    for f in sorted(ROOT.rglob("*.py")):
        if ".git" in f.parts or "_regress" in f.parts:
            continue
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            m = IMPORT.match(line)
            if not m:
                continue
            top = m.group(1)
            if top in sys.stdlib_module_names or top in local or top == "__future__":
                continue
            found.setdefault(top, "%s line %d" % (f.relative_to(ROOT).as_posix(), n))
    return found


def main():
    installs = readme_installs()
    print("README install lines add: %s" % (sorted(installs) or "nothing"))
    missing = 0
    for top, where in sorted(repo_imports().items()):
        want = INSTALL_NAME.get(top, top).lower()
        if want in installs:
            print("ok      %-12s (installed as %s; first used at %s)" % (top, want, where))
        else:
            missing += 1
            print("MISSING %-12s (install name %s; first used at %s)" % (top, want, where))
    print("%d add-on(s) the README does not install -> %s" % (missing, "FAIL" if missing else "PASS"))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
