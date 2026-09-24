#!/usr/bin/env python3
"""Weekly backstop: is every published `-mac` repo still made from its Windows repo's current main?

Build plan V3, section 7f. The real drift check runs at the start of every macgen.py and
publish_pair.py run on Ashley's PC; this is the backstop GitHub runs on a clock (and GitHub
switches such clocks off after 60 quiet days, so the date of the last green run is printed for
the send-folder READMEs to show).

For each of the 25 public repos in harness/public_repos.txt:
    not created yet   there is no <repo>-mac on GitHub
    green             the stamp's main commit is main's current commit, and every file the stamp
                      calls "same" has the stamp's sha256 in both repos
    RED               anything else, with the reason

Usage:  python3 harness/drift.py <out-dir>          exit 1 if any pair is RED
"""
import datetime
import hashlib
import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

GH = "https://github.com/OUTLIERS-ai/"
RAW = "https://raw.githubusercontent.com/OUTLIERS-ai/%s/main/.mac-version.json"


def judge(stamp, main_head, main_sha, mac_sha):
    """State of 1 pair. main_sha / mac_sha: {path: sha256} of each repo's files at HEAD."""
    if not main_head.startswith(stamp["main_commit"][:7]):
        return "RED: made from %s, main is now %s" % (stamp["main_commit"][:7], main_head[:7])
    for f in stamp.get("files", []):
        if f.get("category") != "same":
            continue
        p, want = f["path"], f.get("sha256")
        if main_sha.get(p) != want:
            return "RED: %s differs in the Windows repo from the stamp" % p
        if mac_sha.get(p) != want:
            return "RED: %s differs in the Mac repo from the stamp" % p
    return "green"


def head(url):
    p = subprocess.run(["git", "ls-remote", url, "HEAD"], capture_output=True, text=True, timeout=120)
    return p.stdout.split()[0] if p.returncode == 0 and p.stdout.strip() else None


def tree_sha(url, dest):
    subprocess.run(["git", "-c", "core.autocrlf=false", "clone", "-q", "--depth", "1", url, dest], check=True, timeout=600)
    files = subprocess.run(["git", "-C", dest, "ls-files", "-z"], capture_output=True, text=True, check=True).stdout
    return {f: hashlib.sha256(Path(dest, f).read_bytes()).hexdigest() for f in files.split("\0") if f}


def check_pair(name, tmp):
    mac = name + "-mac"
    mac_head = head(GH + mac)
    if not mac_head:
        return "not created yet"
    try:
        with urllib.request.urlopen(RAW % mac, timeout=60) as r:
            stamp = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return "RED: no readable stamp (%s)" % e
    main_head = head(GH + name) or ""
    return judge(stamp, main_head, tree_sha(GH + name, str(Path(tmp, name))), tree_sha(GH + mac, str(Path(tmp, mac))))


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    out.mkdir(parents=True, exist_ok=True)
    names = [l.strip() for l in (Path(__file__).resolve().parent / "public_repos.txt").read_text().splitlines() if l.strip()]
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for n in names:
            state = check_pair(n, tmp)
            rows.append({"pair": n + "-mac", "state": state})
            print("%-40s %s" % (n + "-mac", state), flush=True)
    red = [r for r in rows if r["state"].startswith("RED")]
    date = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    (out / "drift.json").write_text(json.dumps({"date": date, "pairs": rows, "red": len(red)}, indent=2))
    print("drift %s: %d pairs, %d green, %d not created yet, %d RED" % (
        date, len(rows), sum(r["state"] == "green" for r in rows),
        sum(r["state"] == "not created yet" for r in rows), len(red)))
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())
