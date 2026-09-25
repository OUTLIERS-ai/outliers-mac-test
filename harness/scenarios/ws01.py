"""Picture scenario for the agent-flow Mac guide (wave 6, 2026-09-25).

Runs the situations the agent-flow Mac guide pictures, on 1 test Mac, so every Mac picture shows
words a program really printed: the version checks, status and stop, a settings file agent-flow
would wipe (a comma after the last item, then an empty file), a start that fails because port 3001
is taken, and a server left behind when agent-flow's guard is closed by force.
Record for drawing pictures only; never a "What was run on a Mac" record.
"""
import specs_mac as SM

M = "outliers-ws-01-agent-flow-mac"
ANY = "any"

BREAK_COMMA = ("python3 -c \"import pathlib;p=pathlib.Path.home()/'.claude'/'settings.json';"
               "t=p.read_text().rstrip();k=t.rfind('}');p.write_text(t[:k].rstrip()+',' + chr(10) + '}' + chr(10))\"")
HOLD_3001 = ("nohup python3 -c \"import socket,time;s=socket.socket();"
             "s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('127.0.0.1',3001));"
             "s.listen(5);time.sleep(90)\" >/dev/null 2>&1 & sleep 2; echo listener started")
KILL_GUARD = ("python3 -c \"import json,os,signal;r=json.load(open('logs/agent-flow.pid'));"
              "os.kill(int(r['pid']),signal.SIGKILL);print('guard', r['pid'], 'closed by force')\"; sleep 3")

SPEC = {"steps": SM.prereqs() + [
    SM.run("claude-path", "echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> ~/.zshrc", "scenario", cwd="~"),
    SM.run("v-python", "python3 --version", "scenario", cwd="~"),
    SM.run("v-node", "node --version", "scenario", cwd="~"),
    SM.run("v-git", "git --version", "scenario", cwd="~"),
    SM.run("v-claude", "claude --version", "scenario", cwd="~"),
    SM.run("v-prefix", "python3 -c \"import sys; print(sys.prefix)\"", "scenario", cwd="~"),
    SM.clone(M),
    SM.run("install", "python3 install.py", "scenario", stdin=SM.ENTER, timeout=900),
    SM.run("start", "python3 start.py", "scenario", timeout=300),
    SM.run("status-1", "python3 start.py --status", "scenario", ok=ANY),
    SM.run("stop-1", "python3 start.py --stop", "scenario", ok=ANY),
    SM.run("stop-again", "python3 start.py --stop", "scenario", ok=ANY),
    # a settings file agent-flow would wipe
    SM.check("backup-settings", "cp ~/.claude/settings.json /tmp/settings.good", "harness: keep the good file"),
    SM.check("break-comma", BREAK_COMMA + "; tail -5 ~/.claude/settings.json", "harness: a comma after the last item"),
    SM.run("refused-start", "python3 start.py", "scenario", ok=ANY),
    SM.run("refused-status", "python3 start.py --status", "scenario", ok=ANY),
    SM.run("refused-check", "python3 check_hooks.py", "scenario", ok=ANY),
    SM.check("make-empty", ": > ~/.claude/settings.json; wc -c ~/.claude/settings.json", "harness: an empty settings file"),
    SM.run("empty-check", "python3 check_hooks.py", "scenario", ok=ANY),
    SM.run("empty-start", "python3 start.py", "scenario", ok=ANY),
    SM.check("restore-settings", "cp /tmp/settings.good ~/.claude/settings.json", "harness: put the good file back"),
    # port 3001 taken by another program
    SM.check("hold-3001", HOLD_3001, "harness: another program takes port 3001"),
    SM.run("port-start", "python3 start.py", "scenario", ok=ANY, timeout=300),
    SM.run("port-status", "python3 start.py --status", "scenario", ok=ANY),
    SM.check("free-3001", "sleep 95; echo port free again", "harness: wait for the other program to end", timeout=200),
    # a server left behind
    SM.run("start-2", "python3 start.py", "scenario", ok=ANY, timeout=300),
    SM.check("kill-guard", KILL_GUARD, "harness: close agent-flow's guard by force"),
    SM.run("cleanup-dry", "python3 cleanup.py --dry-run", "scenario", ok=ANY),
    SM.run("cleanup", "python3 cleanup.py", "scenario", ok=ANY),
    SM.run("start-3", "python3 start.py", "scenario", ok=ANY, timeout=300),
    SM.run("status-3", "python3 start.py --status", "scenario", ok=ANY),
    SM.run("stop-3", "python3 start.py --stop", "scenario", ok=ANY),
    SM.run("uninstall", "python3 install.py --uninstall", "scenario", stdin=SM.ENTER, ok=ANY),
]}
