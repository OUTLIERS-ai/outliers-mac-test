#!/usr/bin/env python3
"""Scans every printed output of a member test run for Windows commands and words.

Build plan V3, section 8f and 9a: the strict run passes every step's printed output through the
same rules as check_no_windows.py (a copy of the vault's file, kept byte-identical; the vault's
tests check that). This writes 1 report next to the run record and prints the count. It does
not change the run's verdicts: in wave 0b it is a record; from wave 3 a hit fails the step.

Usage:  /usr/bin/python3 harness/scan_output.py <out-dir>
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_no_windows as CNW  # noqa: E402


def scan_record(path):
    rep = json.loads(Path(path).read_text(encoding="utf-8"))
    hits = []
    for s in rep.get("steps", []):
        for a in s.get("attempts", []):
            if a.get("label") not in ("as printed", "as printed, in PowerShell"):
                continue
            for n, rule, line in CNW.scan_text(a.get("output_tail", ""), "output"):
                hits.append({"step": s["id"], "line": n, "rule": rule, "text": line})
    return hits


def main():
    out = Path(sys.argv[1])
    total = 0
    for rec in sorted(out.glob("*--*.json")):
        hits = scan_record(rec)
        total += len(hits)
        lines = ["%s | %s | line %d | %s | %s" % (rec.stem, h["step"], h["line"], h["rule"], h["text"]) for h in hits]
        (out / ("output-scan-%s.txt" % rec.stem)).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("%s: %d line(s) of printed output break a section 8f rule" % (rec.stem, len(hits)))
        for l in lines[:40]:
            print("  " + l)
    print("OUTPUT SCAN TOTAL: %d" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
