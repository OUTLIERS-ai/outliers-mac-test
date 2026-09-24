#!/usr/bin/env python3
"""Runs one Outliers member repo the way a Mac member would, and writes down what happened.

Usage:  /usr/bin/python3 harness/mactest.py <repo-name> <out-dir>

For every step it first runs the command exactly as the repo's README or guide prints it,
through zsh (the Mac's default shell). If that fails, it tries the obvious Mac substitute
(python3 for python, python3 -m pip for pip, a virtual environment if pip is refused) and
records which one worked. Each step ends with one verdict:

    WORKS                   the printed command worked as printed
    WORKS-WITH-SUBSTITUTE   only a substitute worked; the substitute is recorded
    FAILS                   nothing worked
    NOT-TESTABLE            needs something a public test machine cannot have (a login)

Written to stay runnable on Apple's own /usr/bin/python3 (3.9), so the test tool never
depends on the Python the member steps are testing.
"""
import datetime
import glob
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import specs  # noqa: E402

HOME = Path.home()
UID = os.getuid()
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
VENV = HOME / "outliers-venv"
OLD_WS_COMMITS = {"f6f30d9", "af0e3e5", "bee130f", "d5089ca"}
TAIL = 4000

STATE = {"venv": None, "bg": [], "plists_before": set(), "plists": [], "shots": []}


def now():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def tail(text, n=TAIL):
    text = text or ""
    return text if len(text) <= n else "...[cut]...\n" + text[-n:]


def expand(path, ctx):
    if path is None:
        return str(ctx["repo_dir"])
    path = path.replace("{repo}", str(ctx["repo_dir"]))
    return os.path.expanduser(path)


def env_for_step(extra=None):
    env = dict(os.environ)
    # The member's shell does not carry GitHub's own settings. Keep PATH as the runner has it.
    # The command as printed always runs in a fresh Terminal: no virtual environment the
    # test tool made earlier. Only the Mac substitutes may use one.
    if STATE["venv"] and not STATE.get("as_printed"):
        env["PATH"] = str(VENV / "bin") + ":" + env["PATH"]
        env["VIRTUAL_ENV"] = str(VENV)
    if extra:
        for k, v in extra.items():
            env[k] = os.path.expanduser(v)
    return env


def run_shell(cmd, cwd, stdin="", timeout=600, env_extra=None):
    """Run one command line through zsh, as Terminal would. Returns (code, output, seconds)."""
    t0 = time.time()
    try:
        os.makedirs(cwd, exist_ok=True)
    except OSError:
        pass
    proc = subprocess.Popen(["/bin/zsh", "-c", cmd], cwd=cwd, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                            env=env_for_step(env_extra), start_new_session=True)
    try:
        out, _ = proc.communicate(input=stdin, timeout=timeout)
        code = proc.returncode
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            pass
        out, _ = proc.communicate()
        out = (out or "") + "\n[harness] stopped after %ss (timeout)" % timeout
        code = "timeout"
    return code, out or "", round(time.time() - t0, 1)


# ------------------------------------------------------------------ substitutes
PY_WORD = re.compile(r"(?<![\w/.\-])python(?![\w.\-])")


def mac_substitute(cmd):
    """The obvious Mac rewrite of a command a Windows-first guide printed."""
    new = PY_WORD.sub("python3", cmd)
    new = re.sub(r"(^|&&\s*|;\s*|\|\s*)pip3? install", r"\1python3 -m pip install", new)
    new = re.sub(r"(^|&&\s*|;\s*)playwright install", r"\1python3 -m playwright install", new)
    new = new.replace("$env:USERPROFILE\\.claude\\projectforge\\forge_agent.py",
                      "$HOME/.claude/projectforge/forge_agent.py")
    return new


def make_venv(log):
    if STATE["venv"]:
        return True
    code, out, secs = run_shell("python3 -m venv '%s'" % VENV, str(HOME), timeout=300)
    log.append("made a virtual environment at %s (exit %s)" % (VENV, code))
    if code == 0:
        STATE["venv"] = str(VENV)
        return True
    return False


def looks_failed(code, out, step):
    ok = step.get("ok", [0])
    if ok != "any" and code not in ok:
        return True
    if "Traceback (most recent call last)" in out and not step.get("traceback_ok"):
        return True
    if step.get("expect") and not re.search(step["expect"], out, re.S | re.M):
        return True
    if step.get("refuse") and re.search(step["refuse"], out, re.S | re.M):
        return True
    return False


def run_check(step, ctx):
    chk = step.get("check")
    if not chk:
        return True, ""
    code, out, _ = run_shell(chk, expand(step.get("check_cwd", step.get("cwd")), ctx),
                             timeout=step.get("check_timeout", 120))
    return code == 0, "check `%s` -> exit %s\n%s" % (chk, code, tail(out, 1500))


def attempt(cmd, step, ctx, label):
    STATE["as_printed"] = (label == "as printed")
    try:
        code, out, secs = run_shell(cmd, expand(step.get("cwd"), ctx), step.get("stdin", "\n" * 60),
                                    step.get("timeout", 600), step.get("env"))
    finally:
        STATE["as_printed"] = False
    failed = looks_failed(code, out, step)
    chk_note = ""
    if not failed:
        passed, chk_note = run_check(step, ctx)
        failed = not passed
    return {"label": label, "command": cmd, "exit": code, "seconds": secs,
            "output_tail": tail(out), "check": chk_note, "ok": not failed}


def uses_python_tooling(cmd):
    return bool(re.search(r"(^|[\s;&|(])(python3?|pip3?|playwright|pytest)(\s|$)", cmd))


def do_member_step(step, ctx):
    """As printed first; then the Mac substitute; then a virtual environment if pip refused."""
    attempts = []
    printed = step["cmd"]
    venv_on_before = bool(STATE["venv"])
    a = attempt(printed, step, ctx, "as printed")
    attempts.append(a)
    if a["ok"]:
        return attempts, "WORKS", ""

    subs = list(step.get("subs") or [])
    auto = mac_substitute(printed)
    if not subs and auto != printed:
        subs = [auto]
    if not subs and not step.get("no_auto_retry"):
        # Same command again is pointless; but a module or refusal may still be fixable below.
        subs = []

    notes = []
    for sub in subs:
        b = attempt(sub, step, ctx, "Mac substitute")
        attempts.append(b)
        if b["ok"]:
            return attempts, "WORKS-WITH-SUBSTITUTE", sub
        blob = b["output_tail"]
        # pip refused on a Homebrew-style Python: make a virtual environment and try again.
        if "externally-managed-environment" in blob or "externally managed" in blob:
            if make_venv(notes):
                c = attempt(sub, step, ctx, "Mac substitute inside a virtual environment")
                attempts.append(c)
                if c["ok"]:
                    return attempts, "WORKS-WITH-SUBSTITUTE", "python3 -m venv %s, then: %s" % (VENV, sub)
        m = re.search(r"No module named '?(pytest|playwright)'?", blob)
        if m:
            mod = m.group(1)
            inst = attempt("python3 -m pip install %s" % mod, dict(step, ok=[0], expect=None, check=None),
                           ctx, "install missing %s" % mod)
            attempts.append(inst)
            if not inst["ok"] and "externally-managed" in inst["output_tail"] and make_venv(notes):
                inst = attempt("python3 -m pip install %s" % mod, dict(step, ok=[0], expect=None, check=None),
                               ctx, "install missing %s in a virtual environment" % mod)
                attempts.append(inst)
            if inst["ok"]:
                c = attempt(sub, step, ctx, "Mac substitute after installing %s" % mod)
                attempts.append(c)
                if c["ok"]:
                    return attempts, "WORKS-WITH-SUBSTITUTE", "%s after installing %s%s" % (
                        sub, mod, " in a virtual environment" if STATE["venv"] else "")
    for extra in step.get("then_subs", []):
        c = attempt(extra, step, ctx, "further substitute")
        attempts.append(c)
        if c["ok"]:
            return attempts, "WORKS-WITH-SUBSTITUTE", extra
    return attempts, "FAILS", ""


# ------------------------------------------------------------------ screenshots
def shoot(url, name, ctx, desktop=False):
    out_dir = ctx["out"] / "shots"
    out_dir.mkdir(parents=True, exist_ok=True)
    rec = {"url": url, "files": []}
    base = "%s-%s-%s" % (ctx["repo"], ctx["mac"], name)
    if os.path.exists(CHROME):
        p = out_dir / (base + "-page.png")
        prof = "/tmp/chrome-shot-%s" % name
        code, out, _ = run_shell(
            '"%s" --headless=new --disable-gpu --hide-scrollbars --no-first-run '
            '--user-data-dir=%s --screenshot="%s" --window-size=1440,900 '
            '--virtual-time-budget=9000 "%s"' % (CHROME, prof, p, url), "/tmp", "", 90)
        rec["headless_exit"] = code
        if p.exists():
            rec["files"].append(p.name)
        else:
            rec["headless_output"] = tail(out, 800)
    else:
        rec["headless_exit"] = "Google Chrome not found"
    if desktop:
        p = out_dir / (base + "-desktop.png")
        run_shell('open -a "Google Chrome" "%s" || open "%s"' % (url, url), "/tmp", "", 30)
        time.sleep(8)
        code, out, _ = run_shell('screencapture -x "%s"' % p, "/tmp", "", 30)
        rec["screencapture_exit"] = code
        if p.exists():
            rec["files"].append(p.name)
    STATE["shots"].append(rec)
    return rec


def wait_for_url(url, seconds):
    t_end = time.time() + seconds
    while time.time() < t_end:
        code, out, _ = run_shell("curl -s -o /dev/null -w '%%{http_code}' --max-time 3 '%s'" % url, "/tmp", "", 10)
        if code == 0 and out.strip() not in ("000", ""):
            return out.strip()
        time.sleep(2)
    return None


# ------------------------------------------------------------------ launchd
def list_plists():
    return set(glob.glob(str(HOME / "Library" / "LaunchAgents" / "*.plist")))


def plist_label(p):
    code, out, _ = run_shell("plutil -extract Label raw -o - '%s'" % p, "/tmp", "", 20)
    return out.strip() if code == 0 else None


def launchd_step(step, ctx):
    rec_lines = []
    new = sorted(list_plists() - STATE["plists_before"])
    if step.get("match"):
        new = [p for p in new if re.search(step["match"], p)]
    if not new:
        verdict = "FAILS" if step.get("expect_plist", True) else "WORKS"
        return verdict, "no Mac start-at-login file (LaunchAgent) was written", [], {}
    detail = {}
    all_ok = True
    for p in new:
        label = plist_label(p)
        STATE["plists"].append((p, label))
        info = {"plist": p, "label": label}
        code, out, _ = run_shell("plutil -lint '%s'; echo; cat '%s'" % (p, p), "/tmp", "", 20)
        info["lint_and_contents"] = tail(out, 3000)
        code, out, _ = run_shell("launchctl print gui/%d/%s" % (UID, label), "/tmp", "", 20)
        info["loaded_by_installer"] = (code == 0)
        if code == 0:
            c2, o2, _ = run_shell("launchctl bootout gui/%d/%s" % (UID, label), "/tmp", "", 30)
            info["bootout_before_test"] = {"exit": c2, "out": tail(o2, 500)}
            time.sleep(2)
        c3, o3, _ = run_shell("launchctl bootstrap gui/$(id -u) '%s'" % p, "/tmp", "", 30)
        info["bootstrap"] = {"command": "launchctl bootstrap gui/$(id -u) %s" % p, "exit": c3, "out": tail(o3, 800)}
        time.sleep(step.get("wait", 12))
        c4, o4, _ = run_shell("launchctl print gui/%d/%s" % (UID, label), "/tmp", "", 20)
        m_state = re.search(r"^\s*state = (.+)$", o4, re.M)
        m_pid = re.search(r"^\s*pid = (\d+)", o4, re.M)
        m_exit = re.search(r"last exit code = (.+)$", o4, re.M)
        info["after"] = {"state": m_state.group(1) if m_state else None,
                         "pid": m_pid.group(1) if m_pid else None,
                         "last_exit": m_exit.group(1).strip() if m_exit else None,
                         "print_tail": tail(o4, 1500)}
        ok = c3 == 0
        if step.get("check"):
            passed = False
            chk_out = ""
            for _ in range(step.get("check_tries", 10)):
                c5, chk_out, _ = run_shell(step["check"], expand(step.get("cwd"), ctx), "", 60)
                if c5 == 0:
                    passed = True
                    break
                time.sleep(5)
            info["check"] = {"command": step["check"], "passed": passed, "out": tail(chk_out, 1500)}
            ok = ok and passed
        if step.get("log_glob"):
            code, out, _ = run_shell("for f in %s; do echo \"== $f\"; tail -40 \"$f\"; done" % step["log_glob"],
                                     expand(step.get("cwd"), ctx), "", 20)
            info["job_log"] = tail(out, 2500)
        detail[p] = info
        all_ok = all_ok and ok
    return ("WORKS" if all_ok else "FAILS"), "", [], detail


def launchd_cleanup(ctx):
    notes = []
    for p, label in STATE["plists"]:
        still = os.path.exists(p)
        code, _, _ = run_shell("launchctl print gui/%d/%s" % (UID, label), "/tmp", "", 20)
        loaded = code == 0
        if loaded:
            run_shell("launchctl bootout gui/%d/%s" % (UID, label), "/tmp", "", 30)
        if still:
            try:
                os.remove(p)
            except OSError:
                pass
        notes.append({"plist": p, "left_after_uninstall": still, "still_loaded_after_uninstall": loaded})
    return notes


# ------------------------------------------------------------------ steps
def run_bg(step, ctx):
    """Start a server the way the guide says, wait for its page, photograph it, stop it."""
    attempts = []
    for label, cmd in [("as printed", step["cmd"])] + [("Mac substitute", s) for s in (step.get("subs") or [mac_substitute(step["cmd"])]) if s != step["cmd"]]:
        STATE["as_printed"] = (label == "as printed")
        env = env_for_step(step.get("env"))
        STATE["as_printed"] = False
        logf = ctx["out"] / ("bg-%s-%s.log" % (step["id"], len(attempts)))
        fh = open(logf, "w")
        proc = subprocess.Popen(["/bin/zsh", "-c", cmd], cwd=expand(step.get("cwd"), ctx), stdin=subprocess.PIPE,
                                stdout=fh, stderr=subprocess.STDOUT, text=True, env=env, start_new_session=True)
        up = wait_for_url(step["url"], step.get("wait", 60))
        rec = {"label": label, "command": cmd, "url": step["url"], "http_status": up}
        if up:
            time.sleep(step.get("settle", 4))
            if step.get("check"):
                passed, note = run_check(step, ctx)
                rec["check"] = note
                rec["check_passed"] = passed
            rec["shot"] = shoot(step["url"], step["id"], ctx, desktop=step.get("desktop", False))
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            time.sleep(2)
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            pass
        fh.close()
        rec["output_tail"] = tail(open(logf, errors="replace").read(), 2500)
        rec["exit"] = proc.poll()
        rec["ok"] = bool(up) and rec.get("check_passed", True)
        attempts.append(rec)
        if rec["ok"]:
            return attempts, ("WORKS" if label == "as printed" else "WORKS-WITH-SUBSTITUTE"), ("" if label == "as printed" else cmd)
    return attempts, "FAILS", ""


def run_interactive(step, ctx):
    """A command that opens a window and waits for Enter: let it open, photograph the screen, press Enter."""
    attempts = []
    cands = [("as printed", step["cmd"])]
    sub = (step.get("subs") or [mac_substitute(step["cmd"])])[0]
    if sub != step["cmd"]:
        cands.append(("Mac substitute", sub))
    for label, cmd in cands:
        logf = ctx["out"] / ("int-%s-%s.log" % (step["id"], len(attempts)))
        fh = open(logf, "w")
        STATE["as_printed"] = (label == "as printed")
        env = env_for_step(step.get("env"))
        STATE["as_printed"] = False
        # `script` gives the command a real terminal, as Terminal.app does; without one the
        # sign-in commands refuse ("needs you at the keyboard").
        proc = subprocess.Popen(["/usr/bin/script", "-q", "/dev/null", "/bin/zsh", "-c", cmd],
                                cwd=expand(step.get("cwd"), ctx), stdin=subprocess.PIPE,
                                stdout=fh, stderr=subprocess.STDOUT, text=True, env=env,
                                start_new_session=True)
        time.sleep(step.get("wait", 25))
        alive = proc.poll() is None
        shot = None
        if alive:
            out_dir = ctx["out"] / "shots"
            out_dir.mkdir(parents=True, exist_ok=True)
            p = out_dir / ("%s-%s-%s-desktop.png" % (ctx["repo"], ctx["mac"], step["id"]))
            run_shell('screencapture -x "%s"' % p, "/tmp", "", 30)
            shot = p.name if p.exists() else None
            STATE["shots"].append({"url": step.get("what", "window"), "files": [shot] if shot else []})
            try:
                proc.stdin.write("\n")
                proc.stdin.flush()
            except OSError:
                pass
            try:
                proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
        fh.close()
        out = open(logf, errors="replace").read()
        rec = {"label": label, "command": cmd, "still_waiting_after_s": step.get("wait", 25) if alive else None,
               "exit": proc.poll(), "output_tail": tail(out), "screenshot": shot}
        ok = alive and (not step.get("expect") or re.search(step["expect"], out, re.S | re.M))
        ok = bool(ok) and "Traceback (most recent call last)" not in out
        rec["ok"] = ok
        attempts.append(rec)
        if ok:
            return attempts, ("WORKS" if label == "as printed" else "WORKS-WITH-SUBSTITUTE"), ("" if label == "as printed" else cmd)
    return attempts, "FAILS", ""


def run_step(step, ctx):
    kind = step.get("kind", "run")
    rec = {"id": step["id"], "kind": kind, "what": step.get("what", ""), "source": step.get("source", ""),
           "command_as_printed": step.get("cmd"), "counts": step.get("counts", kind != "prereq"),
           "started": now()}
    try:
        if step.get("not_testable"):
            rec.update(verdict="NOT-TESTABLE", reason=step["not_testable"], attempts=[])
        elif kind == "launchd":
            verdict, reason, attempts, detail = launchd_step(step, ctx)
            rec.update(verdict=verdict, reason=reason, attempts=attempts, launchd=detail)
        elif kind == "serve":
            attempts, verdict, sub = run_bg(step, ctx)
            rec.update(verdict=verdict, substitute=sub, attempts=attempts)
        elif kind == "interactive":
            attempts, verdict, sub = run_interactive(step, ctx)
            rec.update(verdict=verdict, substitute=sub, attempts=attempts)
        elif kind == "check":
            # A check the harness makes itself; there is no printed command to try first.
            a = attempt(step["cmd"], step, ctx, "harness check")
            rec.update(verdict="WORKS" if a["ok"] else "FAILS", attempts=[a], substitute="")
        elif kind == "shot":
            up = wait_for_url(step["url"], step.get("wait", 45))
            rec["http_status"] = up
            if up:
                time.sleep(step.get("settle", 4))
                rec["shot"] = shoot(step["url"], step["id"], ctx, desktop=step.get("desktop", False))
                ok = True
                if step.get("check"):
                    ok, note = run_check(step, ctx)
                    rec["check"] = note
                rec["verdict"] = "WORKS" if ok else "FAILS"
            else:
                rec["verdict"] = "FAILS"
                rec["reason"] = "nothing answered at %s" % step["url"]
            rec["attempts"] = []
        else:
            attempts, verdict, sub = do_member_step(step, ctx)
            rec.update(verdict=verdict, substitute=sub, attempts=attempts)
    except Exception as exc:  # the harness must never stop half way
        rec.update(verdict="FAILS", reason="harness error: %r" % exc, attempts=rec.get("attempts", []))
    rec["finished"] = now()
    return rec


def environment(ctx):
    code, out, _ = run_shell(
        "sw_vers; uname -m; echo; for c in python python3 pip pip3 node npm npx git brew claude; do "
        "printf '%-8s ' $c; command -v $c || echo '(not found)'; done; echo; python3 --version; "
        "/usr/bin/python3 --version; node --version; git --version; echo; "
        "python3 -c 'import sys;print(sys.executable)'; "
        "python3 -m pip --version 2>&1 | head -2; echo; ls -d 'CHROME_PATH' 2>&1; id -u; "
        "launchctl print gui/$(id -u) >/dev/null 2>&1 && echo 'gui domain: present' || echo 'gui domain: missing'"
        .replace("CHROME_PATH", CHROME), str(HOME), "", 60)
    return tail(out, 6000)


def make_it_a_member_mac():
    """GitHub's Macs carry a `python` and a `pip` command that a member's Mac does not have
    (macOS has had no `python` since 12.3; python.org and Homebrew install only `python3`/`pip3`).
    Take them away, so a command printed as `python` fails here exactly as it does for a member."""
    notes = []
    keep = []
    for d in os.environ.get("PATH", "").split(":"):
        has = [n for n in ("python", "pip") if os.path.lexists(os.path.join(d, n))]
        if has and ("Python.framework" in d or "hostedtoolcache" in d):
            notes.append("removed from PATH (runner-only Python folder): %s" % d)
            continue
        for n in has:
            p = os.path.join(d, n)
            code, out, _ = run_shell("sudo mv '%s' '%s.hidden-by-mactest'" % (p, p), "/tmp", "", 30)
            notes.append("hid %s (exit %s)" % (p, code))
        keep.append(d)
    os.environ["PATH"] = ":".join(keep)
    code, out, _ = run_shell("command -v python pip || echo 'python and pip: not found, as on a member Mac'", "/tmp", "", 10)
    notes.append(out.strip())
    return notes


def remote_head(repo):
    code, out, _ = run_shell("git ls-remote https://github.com/OUTLIERS-ai/%s HEAD" % repo, "/tmp", "", 60)
    return out.split()[0][:7] if code == 0 and out.strip() else None


def repo_verdict(steps):
    counted = [s for s in steps if s.get("counts")]
    fails = [s["id"] for s in counted if s.get("verdict") == "FAILS"]
    subs = [s["id"] for s in counted if s.get("verdict") == "WORKS-WITH-SUBSTITUTE"]
    if fails:
        return "FAILS", fails, subs
    if subs:
        return "WORKS-WITH-SUBSTITUTE", fails, subs
    return "WORKS", fails, subs


def write_text(report, path):
    lines = []
    m = report["meta"]
    lines.append("%s on %s (%s, macOS %s)" % (m["repo"], m["mac_label"], m.get("arch"), m.get("macos")))
    lines.append("commit tested: %s   %s" % (m.get("commit"), m.get("commit_status", "")))
    lines.append("REPO VERDICT: %s" % report["verdict"])
    if report["failed_steps"]:
        lines.append("failed steps: %s" % ", ".join(report["failed_steps"]))
    if report["substitute_steps"]:
        lines.append("steps needing a substitute: %s" % ", ".join(report["substitute_steps"]))
    lines.append("")
    lines.append("ENVIRONMENT")
    lines.append(report["environment"])
    for s in report["steps"]:
        lines.append("=" * 78)
        lines.append("[%s] %s  (%s%s)" % (s.get("verdict"), s["id"], s["kind"], "" if s.get("counts") else ", prerequisite"))
        if s.get("what"):
            lines.append("what: %s" % s["what"])
        if s.get("source"):
            lines.append("printed in: %s" % s["source"])
        if s.get("command_as_printed"):
            lines.append("command as printed: %s" % s["command_as_printed"])
        if s.get("substitute"):
            lines.append("substitute used: %s" % s["substitute"])
        if s.get("reason"):
            lines.append("reason: %s" % s["reason"])
        for a in s.get("attempts", []):
            lines.append("-- %s: %s" % (a.get("label"), a.get("command")))
            lines.append("   exit: %s   seconds: %s" % (a.get("exit"), a.get("seconds")))
            if a.get("check"):
                lines.append("   " + a["check"].replace("\n", "\n   "))
            if a.get("screenshot"):
                lines.append("   screenshot: %s" % a["screenshot"])
            if a.get("shot"):
                lines.append("   screenshot: %s" % a["shot"])
            lines.append("   output (tail):")
            lines.append("   " + (a.get("output_tail") or "").replace("\n", "\n   "))
        if s.get("launchd"):
            lines.append(json.dumps(s["launchd"], indent=2))
        if s.get("shot"):
            lines.append("screenshot: %s" % json.dumps(s["shot"]))
    lines.append("=" * 78)
    lines.append("LAUNCHD CLEANUP: %s" % json.dumps(report.get("launchd_cleanup"), indent=2))
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    repo, out = sys.argv[1], Path(sys.argv[2])
    mac_label = os.environ.get("MAC_LABEL", "mac")
    out.mkdir(parents=True, exist_ok=True)
    out = out.resolve()
    os.environ["OUT"] = str(out)
    spec = specs.get(repo)
    STATE["plists_before"] = list_plists()
    ctx = {"repo": repo, "mac": mac_label, "out": out, "repo_dir": HOME / repo}
    meta = {"repo": repo, "mac_label": mac_label, "started": now(),
            "runner_os": os.environ.get("ImageOS"), "image_version": os.environ.get("ImageVersion")}
    _, arch, _ = run_shell("uname -m", "/tmp", "", 10)
    _, ver, _ = run_shell("sw_vers -productVersion", "/tmp", "", 10)
    meta["arch"], meta["macos"] = arch.strip(), ver.strip()
    head = remote_head(repo)
    meta["commit"] = head
    if repo.startswith("outliers-ws-"):
        meta["commit_status"] = "old commit (the 2026-09-23 push; re-push not landed yet)" if head in OLD_WS_COMMITS else "new commit (re-pushed)"
    runner_env = environment(ctx)
    meta["made_like_a_member_mac"] = make_it_a_member_mac()
    report = {"meta": meta, "environment": "BEFORE (runner as GitHub gives it):\n" + runner_env
              + "\n\nCHANGES: " + "; ".join(meta["made_like_a_member_mac"])
              + "\n\nAFTER (what the member steps see):\n" + environment(ctx), "spec_notes": spec.get("notes", []), "steps": []}
    for step in spec["steps"]:
        rec = run_step(step, ctx)
        report["steps"].append(rec)
        print("[%s] %s" % (rec.get("verdict"), step["id"]), flush=True)
    report["launchd_cleanup"] = launchd_cleanup(ctx)
    for s in report["steps"]:
        if s["kind"] == "launchd" and s.get("launchd"):
            s["left_after_uninstall"] = report["launchd_cleanup"]
    report["verdict"], report["failed_steps"], report["substitute_steps"] = repo_verdict(report["steps"])
    report["shots"] = STATE["shots"]
    report["venv_used"] = STATE["venv"]
    meta["finished"] = now()
    base = "%s--%s" % (repo, mac_label)
    (out / (base + ".json")).write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_text(report, out / (base + ".txt"))
    print("REPO VERDICT: %s" % report["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
