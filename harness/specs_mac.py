"""What a Mac member does with each `-mac` repo, step by step, exactly as its Mac guide prints it.

Build plan V3, sections 9a and 9b (wave 6, Session 7, 2026-09-25). Hand-written: 1 entry per
printed step. Every "cmd" is a line the Mac PDF prints (the 2-way check against the PDF is
`Mac-Versions/macgen/check_specs.py` in the vault). The harness runs each exactly as printed, in a
fresh login shell, with no stand-in command (MACTEST_STRICT=1).

2 harness-only steps are not member steps and are not counted:
  * `checkout-pending`: a new `-mac` repo keeps its files on the `pending` branch until the Mac
    test is recorded (9e); the member's clone shows the placeholder `main`, so the harness
    switches to `pending` straight after the printed clone. Only when MACTEST_BRANCH is set.
  * `fingerprint`: the fingerprint of the downloaded files (the same sum as macgen.fingerprint),
    written into the run record, so check_mac_claims.py can prove the PDF describes these files.

MACTEST_FROM_MAIN=1 is the exploratory run made before the `-mac` repo exists: the printed clone
is replaced by a clone of the main repo INTO the `-mac` folder name (programs print the folder they
run from, so their output reads as a Mac member's). Its record says so and is never used for a box.
"""

import os

import specs as W   # the Windows-era helpers and the earlier-part installs

GH = W.GH
ENTER = W.ENTER
CLAUDE_NOT_TESTABLE = "needs your own Claude Code login"
FROM_MAIN = os.environ.get("MACTEST_FROM_MAIN") == "1"
BRANCH = os.environ.get("MACTEST_BRANCH", "")


def run(id_, cmd, source, cwd="{repo}", what="", **kw):
    return W.run(id_, cmd, source, cwd=cwd, what=what, **kw)


def check(id_, cmd, what, cwd="{repo}", **kw):
    d = W.check(id_, cmd, what, cwd=cwd, **kw)
    d.setdefault("counts", False)
    return d


def clone(mac, source="guide, Download"):
    main = mac[:-len("-mac")]
    if FROM_MAIN:
        return {"id": "clone", "kind": "run", "counts": True, "source": source,
                "what": "EXPLORATORY: the main repo cloned into the -mac folder name (no -mac repo yet)",
                "printed": "git clone %s%s" % (GH, mac),
                "cmd": "git clone %s%s %s" % (GH, main, mac), "cwd": "~",
                "check": "test -d ~/%s" % mac, "no_auto_retry": True}
    return {"id": "clone", "kind": "run", "counts": True, "source": source, "what": "copy the repo down",
            "cmd": "git clone %s%s" % (GH, mac), "cwd": "~", "check": "test -d ~/%s" % mac,
            "no_auto_retry": True}


def harness_steps(mac):
    out = []
    if BRANCH and not FROM_MAIN:
        out.append(check("checkout-pending", "git checkout -q %s && git log --oneline -1" % BRANCH,
                         "harness only: switch to the %s branch the files wait on until this test is recorded" % BRANCH))
    out.append({"id": "fingerprint", "kind": "fingerprint", "counts": False, "cwd": "{repo}",
                "what": "harness only: fingerprint of the downloaded files, for check_mac_claims.py"})
    return out


def cd(mac):
    """`cd <repo>-mac` as printed: run as its own step to prove the folder name is right."""
    return run("cd", "cd %s" % mac, "guide, Download", cwd="~", check="test -d ~/%s" % mac)


def prereqs():
    # An earlier part the member already has: their second brain and their CRM. Installed with
    # python3 from the main repos (the -mac repos of those parts come in waves 3 and 4); not counted.
    return [W.prereq("outliers-sb-01-memory"), W.prereq("outliers-crm-01-foundation"), W.claude_code_prereq()]


def pytest_steps(expect, source="guide, 'The safe way to change it'"):
    return [run("pip-pytest", "python3 -m pip install pytest", source, timeout=600),
            run("tests", "python3 -m pytest -q", source, timeout=1200, expect=expect),
            dict(check("tests-full-record", "python3 -m pytest -v -rA -p no:cacheprovider > \"$OUT/pytest-full.log\" 2>&1; "
                       "echo \"pytest exit $?\"; tail -60 \"$OUT/pytest-full.log\"",
                       "the same tests again, every test named, full record kept (diagnosis only)", timeout=1500))]


SPECS = {}

# ------------------------------------------------------------------ agent-flow
M1 = "outliers-ws-01-agent-flow-mac"
SPECS[M1] = {"steps": prereqs() + [
    run("python-version", "python3 --version", "guide, 'What you need'", cwd="~"),
    run("node-version", "node --version", "guide, 'What you need'", cwd="~"),
    clone(M1)] + harness_steps(M1) + [
    cd(M1),
    run("install", "python3 install.py", "guide, Install step 3", stdin=ENTER, timeout=900,
        check="ls ~/Library/LaunchAgents/ && python3 -c \"import json,os;d=json.load(open(os.path.expanduser('~/.claude/settings.json')));print(list(d.get('hooks',{})))\""),
    {"id": "start-at-login", "kind": "launchd", "wait": 20, "cwd": "{repo}", "counts": True,
     "what": "the LaunchAgent the installer wrote: bootstrap it and see if the page on 3001 answers",
     "check": "curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:3001 | grep -E '^(2|3)'", "check_tries": 24,
     "log_glob": "logs/*.log"},
    {"id": "page-3001", "kind": "shot", "url": "http://127.0.0.1:3001", "desktop": True, "wait": 20,
     "what": "the live agent-flow page"},
    run("launchctl-list", "launchctl list | grep outliers", "guide, 'Before you start on a Mac', LaunchAgents", cwd="~"),
    run("status", "python3 start.py --status", "guide, 'Keeping it running'", ok=[0, 1]),
    run("check-hooks", "python3 check_hooks.py", "guide, Install step 9", expect=r"RESULT: OK"),
    run("cleanup-dry-run", "python3 cleanup.py --dry-run", "guide, 'Every command and setting'"),
    run("stop", "python3 start.py --stop", "guide, 'Keeping it running'", ok=[0, 1]),
    run("start", "python3 start.py", "guide, Install step 6", timeout=300,
        check="curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:3001 | grep -E '^(2|3)'"),
    run("stop-2", "python3 start.py --stop", "guide, 'Keeping it running'", ok=[0, 1]),
    run("start-now", "python3 install.py --start-now", "guide, 'Every command and setting'", stdin=ENTER, timeout=600,
        check="curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:3001 | grep -E '^(2|3)'"),
    run("stop-3", "python3 start.py --stop", "guide, 'Keeping it running'", ok=[0, 1]),
] + pytest_steps(r"54 passed, 5 skipped") + [
    run("new-claude-session", "", "guide, Install step 8", not_testable=CLAUDE_NOT_TESTABLE),
    run("uninstall", "python3 install.py --uninstall", "guide, Install tip", stdin=ENTER,
        check="! ls ~/Library/LaunchAgents/ | grep -i agent-flow"),
]}

# ------------------------------------------------------------------ FleetView
M2 = "outliers-ws-02-fleetview-mac"
SPECS[M2] = {"steps": prereqs() + [
    run("node-version", "node --version", "guide, 'What you need'", cwd="~"),
    run("python-version", "python3 --version", "guide, 'What you need'", cwd="~"),
    clone(M2)] + harness_steps(M2) + [
    cd(M2),
    run("install", "python3 install.py", "guide, Install (Enter for every default, yes to start it)", stdin=ENTER, timeout=900,
        check="curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://localhost:3010/graph.html | grep -E '^2'"),
    {"id": "page-3010", "kind": "shot", "url": "http://localhost:3010/graph.html", "desktop": True, "wait": 30,
     "what": "FleetView started by the installer"},
    dict(check("token-panel", "sleep 20; curl -s http://127.0.0.1:3010/api/usage; echo; ! curl -s http://127.0.0.1:3010/api/usage | grep -i 'could not run'",
               "the token panel (no Claude Code sessions exist on this machine)", timeout=120)),
    run("stop", "python3 install.py --stop", "guide, 'Every command and setting'", ok=[0, 1]),
    {"id": "start-at-login", "kind": "launchd", "wait": 15, "counts": True,
     "what": "the LaunchAgent: bootstrap it; the page should answer and the token panel should run",
     "check": "curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://localhost:3010/graph.html | grep -E '^2' && sleep 25 && "
              "echo 'token panel under launchd:' && curl -s http://127.0.0.1:3010/api/usage",
     "check_tries": 6, "log_glob": "fleetview.log"},
    run("launchctl-list", "launchctl list | grep outliers", "guide, 'Before you start on a Mac', LaunchAgents", cwd="~"),
    run("start", "python3 install.py --start", "guide, 'Every command and setting'", ok=[0, 1]),
    run("stop-2", "python3 install.py --stop", "guide, 'Every command and setting'", ok=[0, 1]),
    run("npm-install", "npm install", "guide, 'See it before your own sessions exist'", timeout=600),
    {"id": "demo", "kind": "serve", "cmd": "npm run demo", "url": "http://localhost:3011/graph.html", "wait": 60,
     "source": "guide, 'See it before your own sessions exist'", "desktop": False, "what": "made-up sessions on 3011",
     "counts": True},
    run("npm-test", "npm test", "guide, 'The safe way to change it'", timeout=900, expect=r"# pass 60"),
] + pytest_steps(r"27 passed, 3 skipped") + [
    run("uninstall", "python3 install.py --uninstall", "guide, 'Every command and setting'", stdin=ENTER,
        check="! ls ~/Library/LaunchAgents/ | grep -i fleet"),
]}

# ------------------------------------------------------------------ ProjectForge
M3 = "outliers-ws-03-projectforge-mac"
SPECS[M3] = {"steps": prereqs() + [
    run("python-version", "python3 --version", "guide, 'Before you start'", cwd="~"),
    clone(M3)] + harness_steps(M3) + [
    cd(M3),
    run("install", "python3 install.py", "guide, Install (Enter for every default, including 'Go ahead?')", stdin=ENTER, timeout=600,
        check="test -f data/forge.db && test -f ~/.claude/projectforge/forge_agent.py"),
    {"id": "board", "kind": "serve", "cmd": "python3 forge.py serve", "url": "http://127.0.0.1:3020", "wait": 40,
     "source": "guide, 'Your first day'", "desktop": True, "what": "the web board", "counts": True},
    run("list", "python3 forge.py list", "guide, 'Every command and setting'"),
    run("projects", "python3 forge.py projects", "guide, 'Every command and setting'"),
    run("add-project", "python3 forge.py add-project \"Content week 39\" --dept content --actor you",
        "guide, 'Every command and setting'", ok=[0, 1, 2]),
    run("waiting", "python3 forge.py waiting", "guide, 'Every command and setting'"),
    run("agent-tool", "forge=\"$HOME/.claude/projectforge/forge_agent.py\"\npython3 \"$forge\" open --agent content-lead --dept content --project \"Content week 39\" --title \"Newsletter\" --assignee writer-bot",
        "guide, 'What your agents run'", cwd="~", ok="any", expect=r"(?i)refused|opened|card",
        what="a worker is refused unless a manager was named at install"),
    {"id": "demo-board", "kind": "serve", "cmd": "python3 tools/demo_board.py --out demo --serve", "url": "http://127.0.0.1:3029",
     "wait": 40, "source": "guide, 'Every command and setting'", "what": "the demo board of made-up work", "counts": True},
    run("schedule-print", "python3 tools/schedule.py --print", "guide, 'Every command and setting'"),
    run("start-with-computer", "python3 install.py --start-with-computer --yes", "guide, 'What the installer does'",
        stdin=ENTER, timeout=300),
    {"id": "board-at-login", "kind": "launchd", "wait": 15, "match": "(?i)forge|projectforge", "counts": True,
     "what": "the LaunchAgent that starts the board when you log in: bootstrap it, the board should answer on 3020",
     "check": "curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:3020 | grep -E '^(2|3)'", "check_tries": 12},
    {"id": "board-page-from-login-job", "kind": "shot", "url": "http://127.0.0.1:3020", "wait": 20,
     "what": "the board started by the LaunchAgent"},
    run("launchctl-list", "launchctl list | grep outliers", "guide, 'Before you start on a Mac', LaunchAgents", cwd="~"),
    run("serve-stop", "python3 forge.py serve --stop", "guide, 'Every command and setting'", ok=[0, 1]),
    run("forge-run", "", "guide, '/forge-run in Claude Code'", not_testable=CLAUDE_NOT_TESTABLE),
] + pytest_steps(r"157 passed, 1 skipped") + [
    run("uninstall", "python3 install.py --uninstall", "guide, 'What the installer does'", stdin="y\n" + ENTER, ok=[0],
        check="test ! -f ~/.claude/projectforge/forge_agent.py"),
]}

# ------------------------------------------------------------------ Jeeves
M4 = "outliers-ws-04-jeeves-mac"
SPECS[M4] = {"steps": prereqs() + [
    run("python-version", "python3 --version", "guide, 'Before you start'", cwd="~"),
    clone(M4)] + harness_steps(M4) + [
    cd(M4),
    run("install", "python3 install.py", "guide, Install (Enter for each default)", stdin=ENTER, timeout=600,
        check="test -f config.json && cat config.json"),
    {"id": "jeeves-page", "kind": "serve", "cmd": "python3 start.py", "url": "http://127.0.0.1:4040/", "wait": 40,
     "source": "guide, Install", "desktop": True, "what": "Jeeves over the test vaults", "counts": True,
     "check": "curl -s http://127.0.0.1:4040/api/health"},
    run("demo-data", "python3 tools/demo.py ../jeeves-demo", "guide, 'Try it on made-up data first'", ok=[0, 1], timeout=300),
    {"id": "demo-page", "kind": "serve", "cmd": "python3 tools/demo.py ../jeeves-demo --serve --port 4099",
     "url": "http://127.0.0.1:4099/", "wait": 60, "source": "guide, 'Try it on made-up data first'",
     "what": "Sam the bookkeeper", "counts": True},
    run("launcher", "python3 install.py --launcher --yes", "guide, 'Start it when you log in'", stdin=ENTER, timeout=300),
    {"id": "start-at-login", "kind": "launchd", "wait": 15, "counts": True,
     "what": "the LaunchAgent: bootstrap it; Jeeves should answer on 4040",
     "check": "curl -s --max-time 5 http://127.0.0.1:4040/api/health", "check_tries": 12},
    run("launchctl-list", "launchctl list | grep outliers", "guide, 'Before you start on a Mac', LaunchAgents", cwd="~"),
    run("stop", "python3 start.py --stop", "guide, 'Start and stop'", ok=[0, 1]),
    run("chat", "", "guide, the Chat panel", not_testable=CLAUDE_NOT_TESTABLE),
] + pytest_steps(r"64 passed, 13 skipped") + [
    run("uninstall", "python3 install.py --uninstall", "guide, Uninstall", stdin=ENTER,
        check="! ls ~/Library/LaunchAgents/ | grep -i jeeves"),
]}


def get(repo):
    return SPECS[repo]
