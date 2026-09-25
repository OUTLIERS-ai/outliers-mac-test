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


def fresh_copies():
    """Harness only: a practice copy or private Python folder left by an earlier member test on the
    same Mac (Homebrew order A, then B) is moved aside, so each order starts as a new member does."""
    return check("fresh-copies", "mkdir -p /tmp/earlier-copies; for d in ~/agent-flow-test ~/fleetview-test "
                 "~/projectforge-practice ~/jeeves-trial ~/jeeves-demo ~/outliers-checks; do "
                 "[ -e \"$d\" ] && mv \"$d\" /tmp/earlier-copies/$(basename \"$d\")-$$; done; true",
                 "harness only: move aside copies an earlier member test on this Mac left", cwd="~")


def prereqs():
    # An earlier part the member already has: their second brain and their CRM. Installed with
    # python3 from the main repos (the -mac repos of those parts come in waves 3 and 4); not counted.
    return [W.prereq("outliers-sb-01-memory"), W.prereq("outliers-crm-01-foundation"), W.claude_code_prereq()]


VENV_MAKE = "python3 -m venv ~/outliers-checks"
VENV_PIP = "source ~/outliers-checks/bin/activate && python -m pip install pytest"
VENV_TEST = "source ~/outliers-checks/bin/activate && python -m pytest -q"


def pytest_steps(expect, source="guide, 'The safe way to change it'"):
    # Ruling 2 (wave 6): the self-checks run in a private Python folder, because on Apple Silicon
    # with Homebrew added after python.org a plain `python3 -m pip install` is refused (wave 0a M4,
    # and the exploratory runs of 2026-09-25, Homebrew order B).
    return [run("venv", VENV_MAKE, source, cwd="~", timeout=300),
            run("pip-pytest", VENV_PIP, source, timeout=600),
            run("tests", VENV_TEST, source, timeout=1200, expect=expect),
            dict(check("tests-full-record", "python3 -m pytest -v -rA -p no:cacheprovider > \"$OUT/pytest-full.log\" 2>&1; "
                       "echo \"pytest exit $?\"; tail -60 \"$OUT/pytest-full.log\"",
                       "the same tests again, every test named, full record kept (diagnosis only)", timeout=1500))]


SPECS = {}

# ------------------------------------------------------------------ agent-flow
# Every printed command line of the agent-flow Mac PDF (the guide writer's list,
# D:/Sandbox/wave6-s7-2026-09-25/commands/ws-01.json, checked both ways by check_specs.py).
M1 = "outliers-ws-01-agent-flow-mac"
SPECS[M1] = {"steps": prereqs() + [
    fresh_copies(),
    run("python-prefix", 'python3 -c "import sys; print(sys.prefix)"', "guide, 'Before you start on a Mac'", cwd="~",
        what="the guide's Python check; its answer differs with Homebrew (the guide says what each answer means)"),
    run("node-version", "node --version", "guide, 'What to check'", cwd="~", expect=r"^v(2[2-9]|[3-9][0-9])[.]"),
    run("claude-path", "echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> ~/.zshrc", "guide, 'Before you start on a Mac'", cwd="~"),
    run("claude-version", "claude --version", "guide, 'What to check'", cwd="~", expect=r"[0-9]+[.][0-9]+"),
    run("python-version", "python3 --version", "guide, 'What to check'", cwd="~", expect=r"^Python 3[.](1[1-9]|[2-9][0-9])"),
    run("git-version", "git --version", "guide, 'What to check'", cwd="~", expect=r"^git version"),
    clone(M1, "guide, 'Install it', step 2")] + harness_steps(M1) + [
    cd(M1),
    run("install", "python3 install.py", "guide, 'Install it', step 2", stdin=ENTER, timeout=900,
        check="ls ~/Library/LaunchAgents/ && python3 -c \"import json,os;d=json.load(open(os.path.expanduser('~/.claude/settings.json')));print(list(d.get('hooks',{})))\""),
    {"id": "start-at-login", "kind": "launchd", "wait": 20, "cwd": "{repo}", "counts": True,
     "what": "the LaunchAgent the installer wrote: loaded and started as your Mac would at log-in; the page on 3001 must answer",
     "check": "curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:3001 | grep -E '^(2|3)'", "check_tries": 24,
     "log_glob": "logs/*.log"},
    {"id": "page-3001", "kind": "shot", "url": "http://127.0.0.1:3001", "desktop": True, "wait": 20,
     "what": "the live agent-flow page"},
    run("launchctl-list", "launchctl list | grep outliers", "guide, 'Files the kit makes'", cwd="~", expect=r"com[.]outliers[.]agent-flow"),
    run("status", "python3 start.py --status", "guide, 'Using it day to day'", expect=r"Running for"),
    run("check-hooks", "python3 check_hooks.py", "guide, 'Install it', step 9", expect=r"RESULT: OK"),
    run("stop", "python3 start.py --stop", "guide, 'Using it day to day'", expect=r"Stopped agent-flow|was not running"),
    run("start", "python3 start.py", "guide, 'Install it', step 6", timeout=300,
        check="curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:3001 | grep -E '^(2|3)'"),
    run("stop-2", "python3 start.py --stop", "guide, 'Using it day to day'", expect=r"Stopped agent-flow"),
    run("cleanup", "python3 cleanup.py", "guide, 'When it goes wrong'", expect=r"Registration folder"),
    run("copy", "cp -R outliers-ws-01-agent-flow-mac agent-flow-test", "guide, 'The safe way', step 1", cwd="~",
        check="test -f ~/agent-flow-test/start.py"),
    run("cd-copy", "cd agent-flow-test", "guide, 'The safe way', step 2", cwd="~"),
    run("rm-logs", "rm -rf logs", "guide, 'The safe way', step 2", cwd="~/agent-flow-test", check="test ! -e ~/agent-flow-test/logs"),
    run("venv", VENV_MAKE, "guide, 'The safe way', step 3", cwd="~", timeout=300),
    run("pip-pytest", VENV_PIP, "guide, 'The safe way', step 3", cwd="~", timeout=600),
    run("tests", VENV_TEST, "guide, 'The safe way', step 4", cwd="~/agent-flow-test", timeout=1200, expect=r"54 passed, 5 skipped"),
    run("port-3002", "", "guide, 'When it goes wrong'", printed="python3 install.py --port 3002",
        not_testable="only for a Mac whose port 3001 is taken; the member test keeps the default port"),
    run("autostart", "", "guide, 'Using it day to day'", printed="python3 install.py --autostart",
        not_testable="only after an earlier --no-autostart, which this test does not choose"),
    run("new-claude-session", "", "guide, 'Install it', step 8", printed="claude", not_testable=CLAUDE_NOT_TESTABLE),
    run("uninstall", "python3 install.py --uninstall", "guide, 'Install it', tip", stdin=ENTER,
        check="! ls ~/Library/LaunchAgents/ | grep -i agent-flow"),
]}

# ------------------------------------------------------------------ FleetView
# Every printed command line of the FleetView Mac PDF (commands/ws-02.json, checked by check_specs.py).
M2 = "outliers-ws-02-fleetview-mac"
FV_UP = "curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://localhost:3010/graph.html | grep -E '^2'"
SPECS[M2] = {"steps": prereqs() + [
    fresh_copies(),
    run("git-version", "git --version", "guide, 'Before you start'", cwd="~", expect=r"git version"),
    clone(M2, "guide, 'Install it', step 2")] + harness_steps(M2) + [
    cd(M2),
    run("install", "python3 install.py", "guide, 'Install it', step 2 (Enter for every default, yes to start it)",
        stdin=ENTER, timeout=900, check=FV_UP),
    {"id": "page-3010", "kind": "shot", "url": "http://localhost:3010/graph.html", "desktop": True, "wait": 30,
     "what": "FleetView started by the installer"},
    dict(check("token-panel", "sleep 20; curl -s http://127.0.0.1:3010/api/usage; echo; ! curl -s http://127.0.0.1:3010/api/usage | grep -i 'could not run'",
               "the token panel (no Claude Code sessions exist on this machine)", timeout=120)),
    run("stop", "python3 install.py --stop", "guide, 'Every command and setting'", ok=[0, 1]),
    {"id": "start-at-login", "kind": "launchd", "wait": 15, "counts": True,
     "what": "the LaunchAgent: loaded and started as your Mac would at log-in; the page must answer",
     "check": FV_UP + " && sleep 25 && echo 'token panel under launchd:' && curl -s http://127.0.0.1:3010/api/usage",
     "check_tries": 6, "log_glob": "fleetview.log"},
    run("stop-2", "python3 install.py --stop", "guide, 'Every command and setting'", ok=[0, 1]),
    run("start", "python3 install.py --start", "guide, 'Every command and setting'", expect=r"FleetView (started|is already running)",
        check=FV_UP),
    run("stop-3", "python3 install.py --stop", "guide, 'Every command and setting'", ok=[0, 1]),
    {"id": "watcher", "kind": "serve", "cmd": "node watcher.js", "url": "http://localhost:3010/graph.html", "wait": 40,
     "source": "guide, 'Every command and setting'", "what": "FleetView in this Terminal window", "counts": True},
    {"id": "npm-start", "kind": "serve", "cmd": "npm start", "url": "http://localhost:3010/graph.html", "wait": 40,
     "source": "guide, 'Every command and setting'", "what": "the same, through npm", "counts": True},
    {"id": "demo", "kind": "serve", "cmd": "npm run demo", "url": "http://localhost:3011/graph.html", "wait": 60,
     "source": "guide, 'Install it', tip", "desktop": False, "what": "made-up sessions on 3011", "counts": True},
    run("make-demo", "", "guide, 'Every command and setting'", printed="node tools/make-demo.js <folder> --sessions 30",
        not_testable="a pattern, not a line to type as printed: you put your own folder name where <folder> is"),
    run("npm-test", "npm test", "guide, 'The safe way to change it'", timeout=900,
        # Node's own test runner prints "# pass 60" (no terminal) or an information sign then "pass 60"
        # (nodejs.org's Node): both mean the same, and "fail 0" must follow.
        expect=r"^\S pass 60\s*$.*^\S fail 0\s*$"),
    run("venv", VENV_MAKE, "guide, 'The safe way to change it'", cwd="~", timeout=300),
    run("pip-pytest", VENV_PIP, "guide, 'The safe way to change it'", cwd="~", timeout=600),
    run("tests", VENV_TEST, "guide, 'The safe way to change it'", timeout=1200, expect=r"27 passed, 3 skipped"),
    run("install-yes", "python3 install.py --yes", "guide, 'Every command and setting'", timeout=900, expect=r"config[.]json"),
    run("stop-4", "python3 install.py --stop", "guide, 'Every command and setting'", ok=[0, 1]),
    run("uninstall", "python3 install.py --uninstall", "guide, 'Every command and setting'", stdin=ENTER,
        expect=r"FleetView uninstall", check="! ls ~/Library/LaunchAgents/ | grep -i fleet"),
]}

# ------------------------------------------------------------------ ProjectForge
# Every printed command line of the ProjectForge Mac PDF (commands/ws-03.json, checked by check_specs.py).
M3 = "outliers-ws-03-projectforge-mac"
PF_UP = "curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:3020 | grep -E '^(2|3)'"
SPECS[M3] = {"steps": prereqs() + [
    fresh_copies(),
    run("git-version", "git --version", "guide, 'Before you start'", cwd="~", expect=r"git version"),
    run("venv", VENV_MAKE, "guide, 'Before you start'", cwd="~", timeout=300),
    run("pip-pytest", VENV_PIP, "guide, 'Before you start'", cwd="~", timeout=600),
    clone(M3, "guide, 'Install it', step 2")] + harness_steps(M3) + [
    cd(M3),
    run("install", "python3 install.py", "guide, 'Install it', step 2 (Enter for every default, including 'Go ahead?')",
        stdin=ENTER, timeout=600, check="test -f data/forge.db && test -f ~/.claude/projectforge/forge_agent.py"),
    {"id": "board", "kind": "serve", "cmd": "python3 forge.py serve", "url": "http://127.0.0.1:3020", "wait": 40,
     "source": "guide, 'Your first day'", "desktop": True, "what": "the web board", "counts": True},
    run("projects", "python3 forge.py projects", "guide, 'Every command and setting'"),
    run("add-project", "python3 forge.py add-project \"Content week 39\" --dept content --actor you",
        "guide, 'Adding work from the terminal'", expect=r"pf-p-"),
    run("add-task", "", "guide, 'Adding work from the terminal'",
        printed="python3 forge.py add-task pf-p-5baff3 \"Draft 3 posts\" --status ready --agent writer-bot --actor you",
        not_testable="pf-p-5baff3 stands for your own project's id, which the line before prints"),
    run("agent-tool", "forge=\"$HOME/.claude/projectforge/forge_agent.py\"\n"
        "python3 $forge open --agent content-lead --dept content --project \"Content week 39\" --title \"Newsletter\" --assignee writer-bot",
        "guide, 'What your agents run' (both lines, in 1 Terminal window)", cwd="~", ok="any",
        expect=r"(?i)refused|opened|card", what="a worker is refused unless a manager was named at install"),
    {"id": "demo-board", "kind": "serve", "cmd": "python3 tools/demo_board.py --out demo --serve", "url": "http://127.0.0.1:3029",
     "wait": 40, "source": "guide, 'Every command and setting'", "what": "the demo board of made-up work", "counts": True},
    run("schedule-print", "python3 tools/schedule.py --print", "guide, 'Every command and setting'"),
    run("schedule-remove", "python3 tools/schedule.py --remove", "guide, 'What the download puts on your Mac'", ok=[0, 1]),
    run("prompt-line", "", "guide, idea 8 (a prompt for Claude Code)", printed="python3 tools/schedule.py --install until I say yes.",
        not_testable="a line of a prompt you paste into Claude Code, not a command to type"),
    run("agent-open-pattern", "", "guide, 'Every command and setting'", printed="open --agent <manager> --dept --project --title",
        not_testable="a list of the agents' tool's options, not a line to type as printed"),
    run("start-with-computer", "python3 install.py --start-with-computer", "guide, 'Install it', step 7",
        stdin=ENTER, timeout=300),
    {"id": "board-at-login", "kind": "launchd", "wait": 15, "match": "(?i)forge|projectforge", "counts": True,
     "what": "the LaunchAgent that starts the board when you log in: loaded and started; the board must answer on 3020",
     "check": PF_UP, "check_tries": 12},
    {"id": "board-page-from-login-job", "kind": "shot", "url": "http://127.0.0.1:3020", "wait": 20,
     "what": "the board started by the LaunchAgent"},
    run("launchctl-list", "launchctl list | grep outliers", "guide, 'Before you start on a Mac', LaunchAgents", cwd="~",
        expect=r"ai[.]outliers[.]projectforge"),
    run("serve-stop", "python3 forge.py serve --stop", "guide, 'Every command and setting'", ok=[0, 1]),
    run("tests", VENV_TEST, "guide, 'The safe way to change it'", timeout=1200, expect=r"157 passed, 1 skipped"),
    run("forge-run", "", "guide, '/forge-run in Claude Code'", not_testable=CLAUDE_NOT_TESTABLE),
    run("uninstall", "python3 install.py --uninstall", "guide, 'What the installer does'", stdin="y\n" + ENTER, ok=[0],
        check="test ! -f ~/.claude/projectforge/forge_agent.py"),
]}

# ------------------------------------------------------------------ Jeeves
# Every printed command line of the Jeeves Mac PDF (commands/ws-04.json, checked by check_specs.py).
M4 = "outliers-ws-04-jeeves-mac"
JV = "curl -s --max-time 5 http://127.0.0.1:%d/api/health"


def jeeves_serve(id_, cmd, port, source, **kw):
    d = {"id": id_, "kind": "serve", "cmd": cmd, "url": "http://127.0.0.1:%d/" % port, "wait": 45,
         "source": source, "what": "Jeeves on %d" % port, "counts": True, "check": JV % port}
    d.update(kw)
    return d


SPECS[M4] = {"steps": prereqs() + [
    fresh_copies(),
    run("python-version", "python3 --version", "guide, 'What you need'", cwd="~", expect=r"Python 3"),
    run("python-prefix", 'python3 -c "import sys; print(sys.prefix)"', "guide, 'Before you start on a Mac'", cwd="~",
        what="the guide's Python check; its answer differs with Homebrew (the guide says what each answer means)"),
    run("claude-path", "echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> ~/.zshrc", "guide, 'Before you start on a Mac'", cwd="~"),
    run("claude-version", "claude --version", "guide, 'What you need'", cwd="~", expect=r"Claude Code"),
    run("git-version", "git --version", "guide, 'What you need'", cwd="~", expect=r"git version"),
    clone(M4, "guide, 'Install it', step 2")] + harness_steps(M4) + [
    cd(M4),
    run("install", "python3 install.py", "guide, 'Install it', step 3 (Enter for each default)", stdin=ENTER, timeout=600,
        expect=r"Wrote config[.]json|Nothing changed", check="test -f config.json && cat config.json"),
    jeeves_serve("jeeves-page", "python3 start.py", 4040, "guide, 'Install it', step 8", desktop=True),
    run("stop", "python3 start.py --stop", "guide, 'Stopping it'", expect=r"Stopped Jeeves|not running"),
    jeeves_serve("no-open", "python3 start.py --no-open", 4040, "guide, 'Every command and setting'"),
    run("stop-2", "python3 start.py --stop", "guide, 'Stopping it'", expect=r"Stopped Jeeves|not running"),
    run("install-yes", "python3 install.py --yes", "guide, 'Every command and setting'", timeout=300),
    {"id": "demo-page", "kind": "serve", "cmd": "python3 tools/demo.py ../jeeves-demo --serve --port 4099",
     "url": "http://127.0.0.1:4099/", "wait": 60, "source": "guide, 'Try it on made-up data first'",
     "what": "Sam the bookkeeper", "counts": True},
    run("launcher", "python3 install.py --launcher --yes", "guide, 'Every command and setting'", stdin=ENTER, timeout=300,
        expect=r"LaunchAgents/ai[.]outliers[.]jeeves[.]plist"),
    {"id": "start-at-login", "kind": "launchd", "wait": 15, "counts": True,
     "what": "the LaunchAgent: loaded and started as your Mac would at log-in; Jeeves must answer on 4040",
     "check": JV % 4040, "check_tries": 12},
    run("launchctl-list", "launchctl list | grep outliers", "guide, 'Every command and setting'", cwd="~", expect=r"ai[.]outliers[.]jeeves"),
    run("stop-3", "python3 start.py --stop", "guide, 'Stopping it'", expect=r"Stopped Jeeves|not running"),
    run("copy", "python3 install.py --copy ../jeeves-trial", "guide, 'The safe way to change it'", timeout=300,
        expect=r"Made a copy of Jeeves to experiment on"),
    run("cd-copy", "cd ../jeeves-trial", "guide, 'The safe way to change it'", check="test -d ~/jeeves-trial"),
    run("venv", VENV_MAKE, "guide, 'The safe way to change it'", cwd="~", timeout=300),
    run("pip-pytest", VENV_PIP, "guide, 'The safe way to change it'", cwd="~", timeout=600),
    run("tests", VENV_TEST, "guide, 'The safe way to change it'", cwd="~/jeeves-trial", timeout=1200, expect=r"64 passed, 13 skipped"),
    run("port-install", "python3 install.py --port 4041", "guide, 'When it goes wrong'", stdin=ENTER, timeout=300),
    jeeves_serve("port-start", "python3 start.py --port 4041", 4041, "guide, 'When it goes wrong'"),
    run("stop-4", "python3 start.py --stop", "guide, 'Stopping it'", expect=r"Stopped Jeeves|not running"),
    run("folders", "", "guide, 'Every command and setting'", printed="python3 install.py --vault <folder> --crm <folder> --agents <folder>",
        not_testable="a pattern, not a line to type as printed: you put your own folders where <folder> is"),
    run("config", "", "guide, 'Every command and setting'", printed="python3 start.py --config <file>",
        not_testable="a pattern, not a line to type as printed: you put your own settings file where <file> is"),
    run("today", "", "guide, 'Today'", printed="python3 _engine/today.py --write",
        not_testable="run in your CRM folder; _engine/today.py comes with CRM layer 7, and this test's CRM has layer 1 only"),
    run("chat", "", "guide, the Chat panel", not_testable=CLAUDE_NOT_TESTABLE),
    run("uninstall", "python3 install.py --uninstall", "guide, 'Every command and setting'", stdin=ENTER,
        expect=r"removed|Nothing was set", check="! ls ~/Library/LaunchAgents/ | grep -i jeeves"),
]}


def get(repo):
    return SPECS[repo]
