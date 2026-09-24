#!/usr/bin/env python3
"""CRM layer 5: every command the agent checker prints must work, typed into the member's own
terminal, from a 3rd folder (neither the CRM folder nor `_engine`) whose path has a space.

Found in the wave 1 read (review/wave1-read-other.md, SHOULD 1): from such a folder
`agent_check.py` printed `"../my home/CRM/_agents"/fit-scorer.md`: the folder quoted, then
`/fit-scorer.md` stuck on after the closing quote. zsh on a Mac joins that into 1 argument;
PowerShell on Windows splits it into 2 (`../my home/CRM/_agents` and `/fit-scorer.md`), so the
checker reads the wrong file or the wrong folder. test_hints_run.py splits commands the way a Mac
shell does, so it cannot see this; this test hands every printed command to the real shell.

What it does, in a throwaway folder whose home folder has a space in its name (`my home`):
  1. clones the earlier layers from GitHub and installs them, pressing Enter for every default;
  2. installs the layer under test from the folder this test is run in;
  3. from a 3rd folder (`other folder`, beside `my home`) asks the checker for its usage, typing
     the program's full path, as a member there would;
  4. takes each printed command of the form `python[3] <file>.py ...` (up to 2 spaces in a row,
     where the description starts) and types it into the member's shell from that 3rd folder:
     Windows PowerShell (`powershell.exe`, and `pwsh` too if it is installed) on Windows, zsh on a
     Mac (sh if zsh is missing). The leading `python`/`python3` is swapped for this test's Python.
A command passes only if
  (a) the shell hands Python exactly the arguments the printed line means (read the way a Mac
      shell reads it), checked by running the same line with an argument echo in place of the
      program; and
  (b) run for real through the shell, it prints exactly what the program prints when started
      with those intended arguments directly, and its exit code is the same.

Run from the repo under test:   python3 _mac_regress/test_hints_third_folder.py
Needs the network for the earlier layers. Nothing outside the throwaway folder is touched.
"""
import base64
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path.cwd()
GH = "https://github.com/OUTLIERS-ai/"
LAYERS = ["outliers-crm-01-foundation", "outliers-crm-02-rules", "outliers-crm-03-records",
          "outliers-crm-04-capture", "outliers-crm-05-judgement"]
# The layer's programs whose usage names another file or folder; asked with no arguments.
USAGE = {"outliers-crm-05-judgement": ["agent_check.py"]}
ENTER = "\n" * 60
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
IS_WINDOWS = os.name == "nt"
ECHO = "import sys,json;print(json.dumps(sys.argv[1:]))"
CMD = re.compile(r"(?<![\w/.\-\"])python3?\s+(?P<rest>\S.*)$")


def env_for(home):
    env = dict(os.environ)
    env.update(HOME=str(home), USERPROFILE=str(home), PYTHONIOENCODING="utf-8",
               GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="test@example.com",
               GIT_COMMITTER_NAME="Test", GIT_COMMITTER_EMAIL="test@example.com")
    return env


def run(args, cwd, env, stdin=None, timeout=900):
    try:
        p = subprocess.run(args, cwd=str(cwd), env=env, input=stdin, capture_output=True,
                           timeout=timeout, creationflags=NO_WINDOW)
    except subprocess.TimeoutExpired:
        return "timeout", ""
    return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")


def shells():
    """The member's shell(s): [(name, function turning 1 command line into argv)]."""
    found = []
    if IS_WINDOWS:
        for exe in ("powershell.exe", "pwsh.exe"):
            path = shutil.which(exe)
            if path:
                found.append((exe, lambda line, p=path: [
                    p, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                    "-EncodedCommand", base64.b64encode(line.encode("utf-16-le")).decode("ascii")]))
    else:
        path = shutil.which("zsh") or shutil.which("sh")
        found.append((Path(path).name, lambda line, p=path: [p, "-c", line]))
    return found


def as_typed(line, program_args):
    """The line with the leading `python`/`python3` swapped for this test's Python."""
    if IS_WINDOWS:
        return "& '%s' %s" % (sys.executable.replace("'", "''"), program_args)
    return "%s %s" % (shlex.quote(sys.executable), program_args)


def main():
    repo = HERE.name
    if repo not in LAYERS:
        try:
            url = subprocess.run(["git", "config", "--get", "remote.origin.url"], cwd=str(HERE),
                                 capture_output=True, text=True, creationflags=NO_WINDOW).stdout.strip()
            repo = url.rstrip("/").split("/")[-1].replace(".git", "")
        except OSError:
            pass
    if repo not in USAGE:
        print("REFUSED: %s is not a CRM layer this test covers" % repo)
        return 2

    work = Path(tempfile.mkdtemp(prefix="crm-third-")).resolve()
    home = work / "my home"
    third = work / "other folder"
    home.mkdir()
    third.mkdir()
    env = env_for(home)
    faults = []
    checked = 0
    try:
        for earlier in LAYERS[:LAYERS.index(repo)]:
            dest = work / earlier
            rc, out = run(["git", "clone", "-q", GH + earlier, str(dest)], work, env)
            if rc != 0:
                print("SETUP FAILED: could not clone %s\n%s" % (earlier, out))
                return 2
            rc, out = run([sys.executable, "install.py"], dest, env, stdin=ENTER.encode())
            if rc != 0:
                print("SETUP FAILED: %s installer exit %s\n%s" % (earlier, rc, out[-3000:]))
                return 2
        member = work / "under-test"
        shutil.copytree(str(HERE), str(member),
                        ignore=shutil.ignore_patterns(".git", "_mac_regress", "__pycache__"))
        rc, out = run([sys.executable, "install.py"], member, env, stdin=ENTER.encode())
        crm = home / "CRM"
        print("installer exit %s" % rc)
        if rc != 0 or not (crm / "_layers" / "config.json").exists():
            print("SETUP FAILED: the layer under test did not install\n%s" % out[-3000:])
            return 2

        member_shells = shells()
        print("shells: %s" % ", ".join(n for n, _ in member_shells))
        for program in USAGE[repo]:
            rc, out = run([sys.executable, str(crm / "_engine" / program)], third, env, timeout=300)
            for text in out.splitlines():
                m = CMD.search(text)
                if not m:
                    continue
                program_args = re.split(r"`|\s{2,}|\s#", m.group("rest"), maxsplit=1)[0].strip()
                meant = shlex.split(program_args)
                shown = text.strip()
                direct_rc, direct_out = run([sys.executable] + meant, third, env, timeout=180)
                for name, argv_for in member_shells:
                    checked += 1
                    echo_line = as_typed(text, "-c '%s' %s" % (ECHO, program_args))
                    rc, got = run(argv_for(echo_line), third, env, timeout=180)
                    try:
                        delivered = json.loads(got.strip().splitlines()[-1])
                    except (ValueError, IndexError):
                        delivered = None
                    if delivered != meant:
                        faults.append((name, shown, "the shell hands Python %s, the line means %s"
                                       % (delivered if delivered is not None else got.strip()[-300:],
                                          meant)))
                        continue
                    rc, got = run(argv_for(as_typed(text, program_args)), third, env, timeout=180)
                    if rc != direct_rc or got.replace("\r\n", "\n") != direct_out.replace("\r\n", "\n"):
                        faults.append((name, shown, "typed in: exit %s, %r; meant: exit %s, %r"
                                       % (rc, got.strip()[-200:], direct_rc, direct_out.strip()[-200:])))
                    else:
                        print("ok | %s | %s | exit %s" % (name, shown, rc))
    finally:
        shutil.rmtree(str(work), ignore_errors=True)

    print("%d command(s) typed into a shell from a 3rd folder with a space in its path" % checked)
    for f in faults:
        print("FAULT | %s | %s | %s" % f)
    print("RESULT %s: %d command(s) that do not work as printed"
          % ("FAIL" if faults else "PASS", len(faults)))
    return 1 if faults or checked == 0 else 0


if __name__ == "__main__":
    sys.exit(main())
