#!/usr/bin/env python3
"""Wave s1 (2026-09-26), Mac build plan V3: the key a CRM installer tells a Mac member to press.

The Session 7 ruling (Mac-Versions/review/wave6-apply.md, "Installers' own words"), already applied to
Gather in Session 2: a Mac keyboard's key is Return, so on a Mac every "Press Enter", "or Enter to skip"
and "Enter to ..." an installer prints says Return. Windows prints Enter, exactly as before.

2 checks, run from the repo under test:

  1. The words in the code. Every piece of text in install.py that names the key (Press Enter, Enter to,
     Enter if, or Enter) must come from the KEY setting, never a fixed "Enter": some questions are asked
     only after answers a test cannot give (a file to read, a messages export), so reading the code is
     the only way to cover them. A comment or a docstring does not count; they are never printed.
  2. What is printed. The earlier layers are cloned from GitHub and installed with every offered answer,
     then this layer's installer runs the same way, in a throwaway home folder. On a Mac no printed line
     may name Enter as the key. On Windows at least 1 printed line must still say Enter, so the fix cannot
     change what a Windows member reads (crm-08 prints no key at all and is not covered here).

Run from the repo under test:   python3 _mac_regress/test_return_key.py      (exit 0 = green, 1 = red)
Needs the network for the earlier layers. Nothing outside the throwaway folder is touched.
"""
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tokenize
from pathlib import Path

HERE = Path.cwd()
GH = "https://github.com/OUTLIERS-ai/"
LAYERS = ["outliers-crm-01-foundation", "outliers-crm-02-rules", "outliers-crm-03-records",
          "outliers-crm-04-capture", "outliers-crm-05-judgement", "outliers-crm-06-safety",
          "outliers-crm-07-today"]
ENTER = "\n" * 60
MAC = sys.platform == "darwin"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
KEY_WORDS = re.compile(r"\bPress Enter\b|\bEnter (?:to|if|once)\b|\bor Enter\b")


def repo_name():
    if HERE.name in LAYERS:
        return HERE.name
    url = subprocess.run(["git", "config", "--get", "remote.origin.url"], cwd=str(HERE), capture_output=True,
                         text=True, creationflags=NO_WINDOW).stdout.strip()
    return url.rstrip("/").split("/")[-1].replace(".git", "")


def fixed_words_in_code(path):
    """String pieces of install.py (not comments, not docstrings) that name Enter as the key."""
    src = path.read_text(encoding="utf-8")
    hits = []
    prev = None
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.STRING:
            docstring = prev in (None, tokenize.INDENT, tokenize.NEWLINE, tokenize.DEDENT) and \
                tok.string.lstrip("rRbBuUfF").startswith(('"""', "'''"))
            if not docstring and KEY_WORDS.search(tok.string):
                hits.append("install.py line %d: %s" % (tok.start[0], tok.string.strip()[:100]))
        if tok.type not in (tokenize.NL, tokenize.COMMENT):
            prev = tok.type
    return hits


def env_for(home):
    env = dict(os.environ)
    env.update(HOME=str(home), USERPROFILE=str(home), PYTHONIOENCODING="utf-8",
               GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="test@example.com",
               GIT_COMMITTER_NAME="Test", GIT_COMMITTER_EMAIL="test@example.com")
    return env


def run(args, cwd, env, stdin=None, timeout=900):
    p = subprocess.run(args, cwd=str(cwd), env=env, input=stdin, capture_output=True, timeout=timeout,
                       creationflags=NO_WINDOW)
    return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")


def printed_lines(repo):
    work = Path(tempfile.mkdtemp(prefix="crm-return-"))
    home = work / "home"
    home.mkdir()
    env = env_for(home)
    try:
        for earlier in LAYERS[:LAYERS.index(repo)]:
            dest = work / earlier
            rc, out = run(["git", "clone", "-q", GH + earlier, str(dest)], work, env)
            if rc != 0:
                raise SystemExit("SETUP FAILED: could not clone %s\n%s" % (earlier, out))
            rc, out = run([sys.executable, "install.py"], dest, env, stdin=ENTER.encode())
            if rc != 0:
                raise SystemExit("SETUP FAILED: %s installer exit %d\n%s" % (earlier, rc, out[-3000:]))
        member = work / "under-test"
        shutil.copytree(str(HERE), str(member), ignore=shutil.ignore_patterns(".git", "_mac_regress", "__pycache__"))
        rc, out = run([sys.executable, "install.py"], member, env, stdin=ENTER.encode())
        print("installer exit %d" % rc)
        if rc != 0:
            raise SystemExit("SETUP FAILED: the layer under test did not install\n%s" % out[-3000:])
        return out.splitlines()
    finally:
        shutil.rmtree(str(work), ignore_errors=True)


def main():
    repo = repo_name()
    if repo not in LAYERS:
        print("REFUSED: %s is not a CRM layer whose installer names a key" % repo)
        return 2
    code = fixed_words_in_code(HERE / "install.py")
    for h in code:
        print("FIXED ENTER IN THE CODE | %s" % h)
    lines = printed_lines(repo)
    said = [l.strip() for l in lines if KEY_WORDS.search(l)]
    said_return = [l.strip() for l in lines if re.search(r"\bPress Return\b|\bReturn (?:to|if|once)\b|\bor Return\b", l)]
    print("%d printed lines read; %d name Enter as the key, %d name Return" % (len(lines), len(said), len(said_return)))
    if MAC:
        for l in said:
            print("MAC FAULT | printed | %s" % l)
        bad = bool(code or said) or not said_return
        if not said_return:
            print("MAC FAULT | no printed line names Return: the key sentence was not reached or not changed")
        print("RESULT %s" % ("FAIL" if bad else "PASS"))
        return 1 if bad else 0
    for l in said_return:
        print("WINDOWS CHANGED | printed | %s" % l)
    bad = bool(code) or bool(said_return) or not said
    if not said:
        print("WINDOWS CHANGED | no printed line names Enter any more")
    print("RESULT %s" % ("FAIL" if bad else "PASS"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
