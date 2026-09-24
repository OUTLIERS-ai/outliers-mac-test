"""The Windows-word rules of build plan V3 section 8f, as a text scanner.

A first draft of the rules `check_no_windows.py` will carry (that program is built in wave 0b).
Wave 0a uses it for measurement M7: counting the lines the member programs print that a Mac
member would read as Windows-only.

    python3 harness/windows_words.py --selftest
    python3 harness/windows_words.py <file> [...]      # prints every hit, rule and line
"""
import re
import sys

# `python`, `pip` or `pip3` as the first word of a command, or right after &&, ; or |
# (a leading "$ " or "> " prompt is allowed). `python3` never matches.
CMD_START = re.compile(r"(?:^|&&|;|\|)\s*(?:[$>]\s+)?(python|pip3?)(?=\s|$)")
# The same words used as a command inside a sentence: "type python forge.py serve",
# "run: pip install x". Followed by -m, -c, install, or a .py file.
CMD_IN_TEXT = re.compile(r"(?<!-m )(?<![\w/.\-])(python|pip3?)(?=\s+(?:-m\b|-c\b|install\b|[\w./~\-]*\.py\b))")
VENV_FORM = re.compile(r"source\s+\S*/bin/activate")
WORDS = re.compile(r"\b(Windows key|Windows|PowerShell|Command Prompt|File Explorer|Task Scheduler|"
                   r"Startup folder|schtasks|winget|AppData)\b", re.I)
MARKS = [
    ("drive path", re.compile(r"(?<![\w])[A-Za-z]:\\")),
    ("%NAME%", re.compile(r"%[A-Za-z_][A-Za-z0-9_]*%")),
    ("$env:", re.compile(r"\$env:")),
    ("backslash relative path", re.compile(r"(?<![\w.\\])\.\.?\\")),
    ("Windows file ending", re.compile(r"\.(exe|vbs|cmd|bat|ps1|reg)\b", re.I)),
    ("pythonw", re.compile(r"\bpythonw\b")),
]


def scan_line(line):
    hits = []
    m = CMD_START.search(line) or CMD_IN_TEXT.search(line)
    if m:
        before = line[:m.start(1)]
        if not VENV_FORM.search(before):
            hits.append("command `%s`" % m.group(1))
    for w in WORDS.findall(line):
        hits.append("word `%s`" % w)
    for name, rx in MARKS:
        if rx.search(line):
            hits.append(name)
    return hits


def scan_text(text):
    out = []
    for n, line in enumerate((text or "").splitlines(), 1):
        for h in scan_line(line):
            out.append((n, h, line.strip()))
    return out


MUST_FAIL = [
    "python install.py",
    "  python forge.py serve",
    "cd x && python -m pytest -q",
    "pip install playwright",
    "Next, type python forge.py list to see the cards.",
    "Run: pip install requests",
    "Open PowerShell and type the line",
    "C:\\Users\\you\\Documents",
    "%USERPROFILE%\\.claude",
    "$env:USERPROFILE",
    "wrote Start Jeeves (hidden).vbs",
    "pythonw.exe start.py",
    "open File Explorer",
]
MUST_PASS = [
    "python3 -m pip install x",
    "python3 -m venv .venv && source .venv/bin/activate && pip install playwright",
    "Download Python from python.org",
    "Python 3.13",
    "python3 install.py",
    "Install Certificates.command",
    "zsh: command not found: python",
    "the window opens",
]


def selftest():
    bad = [l for l in MUST_FAIL if not scan_line(l)] + [l for l in MUST_PASS if scan_line(l)]
    for l in bad:
        print("SELFTEST WRONG:", l, scan_line(l))
    print("selftest: %d must-fail, %d must-pass, %d wrong" % (len(MUST_FAIL), len(MUST_PASS), len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        sys.exit(selftest())
    for p in sys.argv[1:]:
        for n, h, line in scan_text(open(p, encoding="utf-8", errors="replace").read()):
            print("%s:%d: %s | %s" % (p, n, h, line))
