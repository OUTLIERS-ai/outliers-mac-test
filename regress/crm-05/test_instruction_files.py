#!/usr/bin/env python3
"""Fault row 19 (build plan V3, section 6b), outliers-crm-05-judgement.

The agent files in `agents/` are instruction files: Claude reads them and acts on them, and the
installer copies the template into the member's CRM as `_agents/_template/`. A line in one that
tells Claude (or the member) to type `python` fails on a Mac. The section 8f rules, as
`harness/check_no_windows.py` applies them to instruction files, are run over every `.md` in
`agents/`; the 1 allowance for instruction files is the Windows command in brackets,
"(on Windows: `...`)", beside the Mac one (plan 7c rule 5).

Instruction files are the same file on both systems, so this is red, then green, on Windows too.

Run from the repo under test:   python3 _mac_regress/test_instruction_files.py
"""
import sys
from pathlib import Path

HERE = Path.cwd()
sys.path.insert(0, str(HERE.parent / "_mactest" / "harness"))
import check_no_windows as CNW  # noqa: E402


def main():
    files = sorted((HERE / "agents").glob("*.md"))
    if not files:
        print("RESULT FAIL: no agent files found in agents/")
        return 1
    hits = 0
    for f in files:
        text = f.read_text(encoding="utf-8")
        for n, rule, line in CNW.scan_text(text, "instruction"):
            print("INSTRUCTION FAULT | agents/%s line %d | %s | %s" % (f.name, n, rule, line))
            hits += 1
    print("%d agent file(s) read, %d hit(s)" % (len(files), hits))
    print("RESULT %s" % ("FAIL" if hits else "PASS"))
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
