#!/usr/bin/env python3
"""CRM layers 2 to 8: every command a layer prints must run from the folder the member is in.

Found in wave 1 (review/wave1-crm.md, "Found, not in any row"): usage text and hints such as
`python ledger.py stats` name a program without its folder. The member runs the CRM's programs
from the CRM folder (every CRM README prints `python _engine/<program>.py ...`), so a hint
without `_engine/` stops with "can't open file", on a Mac and on Windows alike.

Runs the layer the way a member does, in a throwaway home folder:
  1. the earlier layers, cloned from GitHub and installed (pressing Enter for every default);
  2. this layer's installer, from the folder this test is run in (the repo under test);
  3. every command the layer's README prints, then each program's usage, as in
     test_printed_commands.py;
then reads every line printed and every note the installer wrote into the CRM, picks out each
command of the form `python[3] <file>.py ...`, and RUNS it from the folder the member is in when
they run it: the repo folder for `install.py`; for every program, the folder the member ran the
command from that printed it. Each command is run twice, from the CRM folder (each CRM README and
installer says "from inside" the CRM) and from inside `_engine` (where the Layer 2 and Layer 6
guides open the terminal), so a hint must be right from both.
A command fails if its program file is not there, if Python says "can't open file", or if a
file or folder it names (not a <placeholder>) is not there. Placeholders are filled in: <file.csv>
with a made-up export, <note.md> with a note the CRM has, any other <...> with a made-up name;
[optional parts] are left out; a name the member chooses (`your-file.md`) becomes a file already in
that folder. The installer is never run again: for `install.py` the test only
checks that the file is there.

Run from the repo under test:   python3 _mac_regress/test_hints_run.py
Needs the network for the earlier layers. Nothing outside the throwaway folder is touched.
"""
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
          "outliers-crm-04-capture", "outliers-crm-05-judgement", "outliers-crm-06-safety",
          "outliers-crm-07-today", "outliers-crm-08-verification"]
ENTER = "\n" * 60
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# The same README commands and usage calls as regress/crm/test_printed_commands.py.
COMMANDS = {
    "outliers-crm-02-rules": [
        ["_engine/identity.py", "stats"], ["_engine/identity.py", "who", "a name"],
        ["_engine/identity.py", "duplicates"], ["_engine/identity.py", "collisions"],
        ["_engine/schema.py", "contract"], ["_engine/schema.py", "sweep"],
        ["_engine/identity.py", "help"], ["_engine/schema.py", "help"]],
    "outliers-crm-03-records": [
        ["_engine/ledger.py", "types"], ["_engine/ledger.py", "stats"], ["_engine/ledger.py", "tail", "20"],
        ["_engine/derive.py", "show", "a name or link"], ["_engine/derive.py", "quiet", "60"],
        ["_engine/derive.py", "summary"], ["_engine/ledger.py", "help"], ["_engine/derive.py", "help"]],
    "outliers-crm-04-capture": [
        ["_engine/collect.py", "list"],
        ["_engine/collect.py", "run", "connections", "{export}", "--dry-run"],
        ["_engine/collect.py", "run", "connections", "{export}"],
        ["_engine/collect.py", "all"], ["_engine/refresh.py", "due"], ["_engine/refresh.py", "tiers"],
        ["_engine/collect.py", "help"], ["_engine/refresh.py", "help"]],
    "outliers-crm-05-judgement": [
        ["_engine/agent_check.py", "_agents/"], ["_engine/agent_check.py"]],
    "outliers-crm-06-safety": [
        ["_engine/holds.py", "hold", "Someone You Know", "testing the gate"],
        ["_engine/sendgate.py", "Someone You Know"],
        ["_engine/holds.py", "release", "Someone You Know"],
        ["_engine/limits.py"], ["_engine/holds.py", "help"], ["_engine/holds.py", "status"]],
    "outliers-crm-07-today": [
        ["_engine/today.py", "--write"], ["_engine/today.py"]],
    "outliers-crm-08-verification": [
        ["_engine/fourbox.py", "reply_in", "meeting_booked", "--within", "30"],
        ["_engine/watchdog.py"], ["_engine/fourbox.py"]],
}

CMD = re.compile(r"(?<![\w/.\-])python3?\s+(?P<prog>[\w./\\~\-]+\.py)\b(?P<rest>.*)$")


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


def snapshot(folder):
    shot = {}
    if folder.is_dir():
        for p in folder.rglob("*.md"):
            if ".git" not in p.parts:
                shot[p] = p.read_bytes()
    return shot


def parse(text):
    """(program, [arguments]) from 1 printed line, or None. The command ends at a backtick, at
    2 spaces in a row (where usage text starts its description) or at a ' #'."""
    m = CMD.search(text)
    if not m:
        return None
    rest = re.split(r"`|\s{2,}|\s#", m.group("rest"), maxsplit=1)[0]
    rest = re.sub(r"\[[^\]]*\]", " ", rest)            # [optional parts] left out
    try:
        args = shlex.split(rest)
    except ValueError:
        args = rest.split()
    return m.group("prog"), [a for a in args if a not in ("...", "…")]


def fill(arg, export, note, cwd):
    if re.search(r"(^|/)your[-_]", arg):              # "_agents/your-file.md": a name to choose
        folder = cwd / arg.rsplit("/", 1)[0] if "/" in arg else cwd
        mine = sorted(folder.glob("*.md")) if folder.is_dir() else []
        return (str(mine[0]) if mine else arg), not mine
    if "<" in arg and ">" in arg:
        if ".csv" in arg:
            return export, False
        if ".md" in arg:
            return note, False
        return "Someone You Know", False
    return arg, ("/" in arg or arg.endswith((".md", ".csv", ".json"))) and not arg.startswith("-")


def main():
    repo = HERE.name
    if repo not in LAYERS:
        try:
            url = subprocess.run(["git", "config", "--get", "remote.origin.url"], cwd=str(HERE),
                                 capture_output=True, text=True, creationflags=NO_WINDOW).stdout.strip()
            repo = url.rstrip("/").split("/")[-1].replace(".git", "")
        except OSError:
            pass
    if repo not in COMMANDS:
        print("REFUSED: %s is not a CRM layer this test covers" % repo)
        return 2

    work = Path(tempfile.mkdtemp(prefix="crm-hints-"))
    home = work / "home"
    home.mkdir()
    env = env_for(home)
    seen = []  # (where the member reads it, the folder they are in, the line)
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
        crm = home / "CRM"
        before = snapshot(crm)

        member = work / "under-test"
        shutil.copytree(str(HERE), str(member),
                        ignore=shutil.ignore_patterns(".git", "_mac_regress", "__pycache__"))
        rc, out = run([sys.executable, "install.py"], member, env, stdin=ENTER.encode())
        print("installer exit %s" % rc)
        if rc != 0 or not (crm / "_layers" / "config.json").exists():
            print("SETUP FAILED: the layer under test did not install\n%s" % out[-3000:])
            return 2
        # The installer's own lines: `install.py` is run from the repo folder; every program
        # it names is run from the CRM folder, as each installer and README says.
        seen += [("installer", None, l) for l in out.splitlines()]
        for p, data in sorted(snapshot(crm).items()):
            if before.get(p) != data:
                where = "note " + p.relative_to(crm).as_posix()
                seen += [(where, crm, l) for l in data.decode("utf-8", "replace").splitlines()]

        export = home / "exports" / "connections.csv"
        export.parent.mkdir(parents=True, exist_ok=True)
        export.write_text("First Name,Last Name,URL,Email Address,Company,Position,Connected On\n"
                          "Sam,Testperson,https://www.linkedin.com/in/sam-testperson-000,,Made Up Ltd,Owner,"
                          "01 Sep 2026\n", encoding="utf-8")
        # Each command once from the CRM folder (as the READMEs and installers print it) and
        # once from inside `_engine` (where the Layer 2 and Layer 6 guides open the terminal).
        engine = crm / "_engine"
        for cmd in COMMANDS[repo]:
            args = [a.replace("{export}", str(export)) for a in cmd]
            rc, out = run([sys.executable] + args, crm, env, timeout=300)
            seen += [("python %s" % " ".join(cmd), crm, l) for l in out.splitlines()]
            inside = [args[0].replace("_engine/", "", 1)] + args[1:]
            rc, out = run([sys.executable] + inside, engine, env, timeout=300)
            seen += [("in _engine: python %s" % " ".join(inside), engine, l) for l in out.splitlines()]

        note = next((str(p) for p in sorted(crm.rglob("*.md")) if ".git" not in p.parts), "README.md")
        done = set()
        for where, cwd, text in seen:
            got = parse(text)
            if not got:
                continue
            prog, args = got
            if cwd is None:
                cwd = member if prog.endswith("install.py") else crm
            key = (str(cwd), prog, tuple(args))
            if key in done:
                continue
            done.add(key)
            checked += 1
            shown = text.strip()
            if not (cwd / prog).is_file():
                faults.append((where, shown, "no file %s in the folder the member is in (%s)"
                               % (prog, {member: "the repo folder", crm: "the CRM folder"}.get(cwd, "_engine"))))
                continue
            if prog.endswith("install.py"):
                continue
            filled = []
            for a in args:
                value, is_path = fill(a, str(export), note, cwd)
                if is_path and not (cwd / value).exists():
                    faults.append((where, shown, "names %s, which is not there" % a))
                filled.append(value)
            rc, out = run([sys.executable, prog] + filled, cwd, env, timeout=180)
            if "can't open file" in out or rc == "timeout":
                faults.append((where, shown, "ran: exit %s: %s" % (rc, out.strip()[-300:])))
    finally:
        shutil.rmtree(str(work), ignore_errors=True)

    print("%d printed or written lines read, %d distinct commands run or checked" % (len(seen), checked))
    for f in faults:
        print("FAULT | %s | %s | %s" % f)
    print("RESULT %s: %d command(s) a member cannot run from where they are"
          % ("FAIL" if faults else "PASS", len(faults)))
    return 1 if faults or checked == 0 else 0


if __name__ == "__main__":
    sys.exit(main())
