"""Wave 0a M7: after the member walk, run every command-line program in the repo with --help
and keep its whole output, so the lines a member reads there can be scanned too.

Usage: /usr/bin/python3 harness/help_sweep.py <repo> <out-dir>

A program counts when its file uses argparse. Tests, virtual environments and git folders are
skipped. Each program gets 30 seconds, no keyboard input, and runs from the repo folder.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

SKIP = {"tests", "test", ".git", ".venv", "venv", "node_modules", "__pycache__"}


def main():
    repo, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    root = Path.home() / repo
    venv_py = Path.home() / "outliers-venv" / "bin" / "python3"
    py = str(venv_py) if venv_py.exists() else "python3"
    rows = []
    for p in sorted(root.rglob("*.py")):
        rel = p.relative_to(root)
        if any(part in SKIP for part in rel.parts):
            continue
        try:
            src = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "argparse" not in src or "add_argument" not in src:
            continue
        try:
            r = subprocess.run([py, str(rel), "--help"], cwd=str(root), stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
            text, code = r.stdout.decode("utf-8", "replace"), r.returncode
        except subprocess.TimeoutExpired as e:
            text, code = (e.stdout or b"").decode("utf-8", "replace") + "\n[help_sweep] timeout", "timeout"
        rows.append({"file": str(rel), "command": "%s %s --help" % (os.path.basename(py), rel),
                     "exit": code, "output": text})
        print("[help] %s exit %s" % (rel, code), flush=True)
    (out / ("help-%s.json" % repo)).write_text(json.dumps({"repo": repo, "python": py, "programs": rows}, indent=2),
                                             encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
