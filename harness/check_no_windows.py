# -*- coding: utf-8 -*-
"""check_no_windows.py -- fails anything a Mac member reads that shows a Windows command, path or word.

For future Claude: build plan V3 section 8f. The job of the whole Mac build is that a Mac member
never meets a Windows instruction; this program is that job, checked by a program. It reads:

    a PDF          every page's text, plus the words OCR reads in every picture inside it
    a picture      the words OCR reads in it (.png, .jpg, .jpeg)
    a text file    every line (README, guide Markdown, a program's printed output, a served page's text)

Rules come from 8f and were first drafted as harness/windows_words.py in wave 0a (M7). They are
never widened to make something pass: an accepted exception is written per repo in its settings
file (`windows_words_ok`, with a reason) and the count of those is printed on every run.

    python check_no_windows.py <file> [...]                  # member files and PDFs
    python check_no_windows.py --kind instruction <file>     # an instruction file Claude reads
    python check_no_windows.py --kind output <file>          # printed program output
    python check_no_windows.py --selftest                    # the must-fail and must-pass lines

Exit 0 = PASS (no hit), 1 = FAIL (hits printed with file, page and line), 2 = could not read.
"""
import argparse
import io
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- the rules (8f)
# `python`, `pip` or `pip3` as the first word of a command, or right after &&, ; or |
# (a leading "$ " or "> " prompt is allowed). `python3` never matches.
CMD_START = re.compile(r"(?:^|&&|;|\|)\s*(?:[$>]\s+)?(python|pip3?)(?=\s|$)")
# The same words used as a command inside a sentence: "type python forge.py serve",
# "run: pip install x". Followed by -m, -c, install, or a .py file.
CMD_IN_TEXT = re.compile(r"(?<!-m )(?<![\w/.\-])(python|pip3?)(?=\s+(?:-m\b|-c\b|install\b|[\w./~\-]*\.py\b))")
# The private-folder form: pip or python after `source .../bin/activate` earlier in the line.
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

# ---------------------------------------------------------------- what is allowed (8f)
# The 1 pointer line: "On Windows? Use <main repo>" or macgen's "On Windows, use <main repo>".
POINTER = re.compile(r"On Windows[?,]\s+use\s+\[?`?(?:https://github\.com/OUTLIERS-ai/)?"
                     r"(?:outliers-[\w\-]+|fathom-meeting-agent)`?\]?(?:\([^)]*\))?\.?", re.I)
# Ashley's own history pictures keep their caption.
CAPTION = re.compile(r"\(Ashley's Windows PC\)\s*$")
# Instruction files only: the both-systems wording "(on Windows: `...`)".
BRACKETED_WINDOWS = re.compile(r"\(on Windows: `[^`]*`\)")

KINDS = ("member", "instruction", "output")


def strip_allowed(line, kind="member"):
    """The line with its allowed parts (8f) taken out; everything left is scanned."""
    if kind not in KINDS:
        raise ValueError("kind must be one of %s" % (KINDS,))
    line = POINTER.sub("", line)
    line = CAPTION.sub("", line)
    if kind == "instruction":
        line = BRACKETED_WINDOWS.sub("", line)
    return line


def scan_line(line, kind="member"):
    """Every rule the line breaks, as short names. An empty list means the line passes."""
    line = strip_allowed(line, kind)
    hits = []
    m = CMD_START.search(line) or CMD_IN_TEXT.search(line)
    if m and not VENV_FORM.search(line[:m.start(1)]):
        hits.append("command `%s`" % m.group(1))
    for w in WORDS.findall(line):
        hits.append("word `%s`" % w)
    for name, rx in MARKS:
        if rx.search(line):
            hits.append(name)
    return hits


def scan_text(text, kind="member"):
    """[(line number, rule, line)] for every hit."""
    out = []
    for n, line in enumerate((text or "").splitlines(), 1):
        for h in scan_line(line, kind):
            out.append((n, h, line.strip()))
    return out


# ---------------------------------------------------------------- readers
_OCR = None


def _ocr_engine():
    global _OCR
    if _OCR is None:
        from rapidocr_onnxruntime import RapidOCR
        _OCR = RapidOCR()
    return _OCR


def ocr_lines(image_bytes, tile=1400, overlap=120):
    """Words OCR reads in a picture, tiled so small type in a tall picture is still read."""
    from PIL import Image
    import numpy as np
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w, h = img.size
    if w < 8 or h < 8:
        return []
    lines, top = [], 0
    while True:
        box = img.crop((0, top, w, min(h, top + tile)))
        res, _ = _ocr_engine()(np.array(box))
        lines.extend(_join_into_lines(res or []))
        if top + tile >= h:
            break
        top += tile - overlap
    return lines


def _join_into_lines(res):
    """OCR hands back word fragments in no fixed order. Put fragments whose middles sit at the
    same height into 1 line, left to right, so "Open" "Power" "Shell" reads as a line."""
    items = []
    for box, text, _score in res:
        ys = [p[1] for p in box]
        xs = [p[0] for p in box]
        items.append(((min(ys) + max(ys)) / 2, max(ys) - min(ys), min(xs), text))
    items.sort()
    lines, cur, cur_y, cur_h = [], [], None, None
    for y, hgt, x, text in items:
        if cur and abs(y - cur_y) > max(cur_h, hgt) * 0.5:
            lines.append(" ".join(t for _, t in sorted(cur)))
            cur = []
        if not cur:
            cur_y, cur_h = y, hgt
        cur.append((x, text))
    if cur:
        lines.append(" ".join(t for _, t in sorted(cur)))
    return lines


# The word list with spaces taken out, for OCR text, where 1 word is often read as 2 pieces.
_OCR_WORDS = [w.replace(" ", "").lower() for w in
              ("Windows key", "Windows", "PowerShell", "Command Prompt", "File Explorer",
               "Task Scheduler", "Startup folder", "schtasks", "winget", "AppData")]


def ocr_extra_hits(line):
    """Windows words OCR split into pieces ("Power Shell"), found by reading the line joined up."""
    joined = re.sub(r"\s+", "", line).lower()
    found = [w for w in _OCR_WORDS if w in joined]
    # "windowskey" contains "windows": report the longest only
    found = [w for w in found if not any(w != o and w in o for o in found)]
    return ["word `%s` (OCR, pieces joined)" % w for w in found]


def read_pdf(path, with_ocr=True):
    """[(where, text)] for each page's text and each picture's OCR text."""
    import fitz
    parts = []
    with fitz.open(str(path)) as doc:
        for i, page in enumerate(doc, 1):
            parts.append(("page %d" % i, page.get_text("text")))
            if with_ocr:
                for j, info in enumerate(page.get_images(full=True), 1):
                    try:
                        pix = fitz.Pixmap(doc, info[0])
                        if pix.n - pix.alpha >= 4:
                            pix = fitz.Pixmap(fitz.csRGB, pix)
                        data = pix.tobytes("png")
                    except Exception as exc:  # a picture we cannot read is reported, never skipped
                        parts.append(("page %d picture %d" % (i, j), "[unreadable picture: %s]" % exc))
                        continue
                    parts.append(("page %d picture %d (OCR)" % (i, j), "\n".join(ocr_lines(data))))
    return parts


_BLOCK_END = re.compile(r"<br\s*/?>|</(?:p|div|li|tr|td|th|h[1-6]|pre|table|ul|ol|section|figure)>", re.I)


def html_visible_text(html):
    """What a member sees on an HTML page: no <style>, <script> or comments, tags removed,
    a line break wherever the page starts a new line. The page's own CSS (`.cmd {...}`) is code,
    not something a member reads."""
    import html as H
    html = re.sub(r"(?is)<(style|script)\b.*?</\1>", "", html)
    html = re.sub(r"(?s)<!--.*?-->", "", html)
    html = _BLOCK_END.sub("\n", html)
    html = re.sub(r"(?s)<[^>]+>", "", html)
    return "\n".join(l.strip() for l in H.unescape(html).splitlines() if l.strip())


def read_any(path, with_ocr=True):
    p = Path(path)
    suf = p.suffix.lower()
    if suf == ".pdf":
        return read_pdf(p, with_ocr)
    if suf in (".html", ".htm"):
        return [("page text", html_visible_text(p.read_text(encoding="utf-8", errors="replace")))]
    if suf in (".png", ".jpg", ".jpeg"):
        if not with_ocr:
            return [("picture (OCR off)", "")]
        return [("picture (OCR)", "\n".join(ocr_lines(p.read_bytes())))]
    return [("", p.read_text(encoding="utf-8", errors="replace"))]


def check_file(path, kind="member", with_ocr=True, allowed=()):
    """[(file, where, line, rule, text)] for every hit not on the `allowed` list.

    `allowed` is the repo's windows_words_ok list: dicts with `path`, `text` (the exact line,
    stripped) and `reason`. A hit is allowed only when path and whole line both match."""
    hits = []
    ok = {(a["path"], a["text"]) for a in allowed}
    for where, text in read_any(path, with_ocr):
        found = scan_text(text, kind)
        if "OCR" in where:
            already = {(n, r.split("`")[1].replace(" ", "").lower()) for n, r, _ in found if r.startswith("word")}
            for n, line in enumerate(text.splitlines(), 1):
                for r in ocr_extra_hits(strip_allowed(line, kind)):
                    if (n, r.split("`")[1]) not in already:
                        found.append((n, r, line.strip()))
        for n, rule, line in found:
            if (Path(path).as_posix(), line) in ok or (Path(path).name, line) in ok:
                continue
            hits.append((str(path), where, n, rule, line))
    return hits


# ---------------------------------------------------------------- self-test
MUST_FAIL = [
    "python install.py",
    "  python forge.py serve",
    "cd x && python -m pytest -q",
    "pip install playwright",
    "pip3 install requests",
    "Next, type python forge.py list to see the cards.",
    "Run: pip install requests",
    "Open PowerShell and type the line",
    "C:\\Users\\you\\Documents",
    "%USERPROFILE%\\.claude",
    "$env:USERPROFILE",
    "wrote Start Jeeves (hidden).vbs",
    "pythonw.exe start.py",
    "open File Explorer",
    "Press the Windows key",
    "schtasks /create",
    "winget install Python",
    "..\\engine\\run.py",
]
MUST_PASS = [
    "python3 -m pip install x",
    "python3 -m venv .venv && source .venv/bin/activate && pip install playwright",
    "python3 -m venv .venv && source .venv/bin/activate && python -m pip install requests",
    "Download Python from python.org",
    "Python 3.13",
    "python3 install.py",
    "Install Certificates.command",
    "zsh: command not found: python",
    "the window opens",
    "**This is the Mac version.** On Windows, use [outliers-crm-02-rules](https://github.com/OUTLIERS-ai/outliers-crm-02-rules).",
    "On Windows? Use outliers-ws-03-projectforge",
    "The board, as it looked on the day (Ashley's Windows PC)",
]


def selftest():
    bad = [l for l in MUST_FAIL if not scan_line(l)] + [l for l in MUST_PASS if scan_line(l)]
    for l in bad:
        print("SELFTEST WRONG:", l, scan_line(l))
    print("selftest: %d must-fail, %d must-pass, %d wrong" % (len(MUST_FAIL), len(MUST_PASS), len(bad)))
    return 1 if bad else 0


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--kind", default="member", choices=KINDS)
    ap.add_argument("--no-ocr", action="store_true", help="skip pictures (the run report says so)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.files:
        ap.error("name at least 1 file")
    total, unreadable = 0, 0
    for f in a.files:
        try:
            hits = check_file(f, a.kind, with_ocr=not a.no_ocr)
        except Exception as exc:
            print("CANNOT READ %s: %s" % (f, exc))
            unreadable += 1
            continue
        for path, where, n, rule, line in hits:
            print("%s%s line %d: %s | %s" % (path, (" " + where) if where else "", n, rule, line))
        total += len(hits)
    print("check_no_windows: %d file(s), %d hit(s)%s%s -> %s" % (
        len(a.files), total, ", %d unreadable" % unreadable if unreadable else "",
        ", pictures NOT read (OCR off)" if a.no_ocr else "",
        "FAIL" if total else ("NOT PROVEN" if unreadable else "PASS")))
    if total:
        return 1
    return 2 if unreadable else 0


if __name__ == "__main__":
    sys.exit(main())
