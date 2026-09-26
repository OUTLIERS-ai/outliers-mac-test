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
                 "~/projectforge-practice ~/jeeves-trial ~/jeeves-demo ~/outliers-checks ~/fleetview-busy-day ~/my-screen ~/.local/lib/node_modules/ccusage; do "
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
# Every printed command line of the agent-flow Mac PDF, inside sentences too (commands/ws-01.json,
# round 2 of 2026-09-25; checked both ways by check_specs.py).
M1 = "outliers-ws-01-agent-flow-mac"
AF_UP = "curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:3001 | grep -E '^(2|3)'"
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
    run("install", "python3 install.py", "guide, 'Install it', step 3", stdin=ENTER, timeout=900,
        expect=r"each event now has exactly 1|1 copy per event",
        check="ls ~/Library/LaunchAgents/ && python3 -c \"import json,os;d=json.load(open(os.path.expanduser('~/.claude/settings.json')));print(list(d.get('hooks',{})))\""),
    {"id": "start-at-login", "kind": "launchd", "wait": 20, "cwd": "{repo}", "counts": True,
     "what": "the LaunchAgent the installer wrote: switched on and started as your Mac does when you sign in; the page on 3001 must answer",
     "check": AF_UP, "check_tries": 24, "log_glob": "logs/*.log"},
    {"id": "page-3001", "kind": "shot", "url": "http://127.0.0.1:3001", "desktop": True, "wait": 20,
     "what": "the live agent-flow page"},
    run("status", "python3 start.py --status", "guide, 'Using it day to day'", expect=r"Running for"),
    run("check-hooks", "python3 check_hooks.py", "guide, 'Install it', step 9", expect=r"RESULT: OK"),
    run("stop", "python3 start.py --stop", "guide, 'Using it day to day'", expect=r"Stopped agent-flow|was not running"),
    run("start", "python3 start.py", "guide, 'Install it', step 6", timeout=300, check=AF_UP),
    run("stop-2", "python3 start.py --stop", "guide, 'Using it day to day'", expect=r"Stopped agent-flow"),
    run("cleanup", "python3 cleanup.py", "guide, 'When it goes wrong'", expect=r"Registration folder"),
    run("launchctl-list", "launchctl list | grep outliers", "guide, 'Files the kit makes'", cwd="~", expect=r"com[.]outliers[.]agent-flow"),
    run("copy", "cp -R outliers-ws-01-agent-flow-mac agent-flow-test", "guide, 'The safe way', step 1", cwd="~",
        check="test -f ~/agent-flow-test/start.py"),
    run("cd-copy", "cd agent-flow-test", "guide, 'The safe way', step 2", cwd="~", check="test -d ~/agent-flow-test"),
    run("rm-logs", "rm -rf logs", "guide, 'The safe way', step 2", cwd="~/agent-flow-test", check="test ! -e ~/agent-flow-test/logs"),
    run("venv", VENV_MAKE, "guide, 'The safe way', step 3", cwd="~", timeout=300),
    run("pip-pytest", VENV_PIP, "guide, 'The safe way', step 3", cwd="~/agent-flow-test", timeout=600,
        expect=r"Successfully installed|Requirement already satisfied"),
    run("tests", VENV_TEST, "guide, 'The safe way', step 4 (in the copy)", cwd="~/agent-flow-test", timeout=1200,
        expect=r"54 passed, 5 skipped"),
    run("cd-back", "cd ../outliers-ws-01-agent-flow-mac", "guide, 'The safe way', step 5", cwd="~/agent-flow-test",
        check="test -d ~/outliers-ws-01-agent-flow-mac"),
    run("port-3002", "", "guide, 'When it goes wrong'", printed="python3 install.py --port 3002",
        not_testable="it is only for a Mac whose port 3001 is already taken, and on the test Macs it was free"),
    run("autostart", "", "guide, 'Using it day to day'", printed="python3 install.py --autostart",
        not_testable="it only matters after an earlier --no-autostart, which the test did not choose"),
    run("new-claude-session", "", "guide, 'Install it', step 8", printed="claude",
        not_testable="it opens Claude Code, which needs your own login"),
    run("npx-by-hand", "", "guide, 'Worth knowing'", printed="npx agent-flow-app",
        not_testable="this guide tells you never to run it by hand while the kit is installed"),
    run("uninstall", "python3 install.py --uninstall", "guide, 'Install it', tip", stdin=ENTER,
        check="! ls ~/Library/LaunchAgents/ | grep -i agent-flow"),
]}

# ------------------------------------------------------------------ FleetView
# Every printed command line of the FleetView Mac PDF, inside sentences too (commands/ws-02.json, round 2).
M2 = "outliers-ws-02-fleetview-mac"
FV_UP = "curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://localhost:3010/graph.html | grep -E '^2'"
NPM_60 = r"^\S pass 60\s*$.*^\S fail 0\s*$"   # "# pass 60" or an information sign then "pass 60"
SPECS[M2] = {"steps": prereqs() + [
    fresh_copies(),
    run("python-prefix", 'python3 -c "import sys; print(sys.prefix)"', "guide, 'Before you start on a Mac'", cwd="~",
        what="the guide's Python check; its answer differs with Homebrew (the guide says what each answer means)"),
    run("node-version", "node --version", "guide, 'Before you start'", cwd="~", expect=r"^v(2[2-9]|[3-9][0-9])[.]"),
    run("claude-path", "echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> ~/.zshrc", "guide, 'Before you start on a Mac'", cwd="~"),
    run("claude-version", "claude --version", "guide, 'Before you start'", cwd="~", expect=r"Claude Code"),
    run("python-version", "python3 --version", "guide, 'Before you start'", cwd="~", expect=r"^Python 3[.](1[1-9]|[2-9][0-9])"),
    run("git-version", "git --version", "guide, 'Before you start'", cwd="~", expect=r"git version"),
    run("ls-projects", "", "guide, 'Before you start'", printed="ls ~/.claude/projects",
        not_testable="the test Macs have never run a Claude Code session, so this folder does not exist on them; it lists your projects once you have used Claude Code"),
    clone(M2, "guide, 'Install it', step 2")] + harness_steps(M2) + [
    cd(M2),
    run("install", "python3 install.py", "guide, 'Install it', step 2 (Return for every default, yes to start it)",
        stdin=ENTER, timeout=900, expect=r"FleetView started in the background|FleetView is already running", check=FV_UP),
    {"id": "page-3010", "kind": "shot", "url": "http://localhost:3010/graph.html", "desktop": True, "wait": 30,
     "what": "FleetView started by the installer"},
    dict(check("token-panel", "sleep 20; curl -s http://127.0.0.1:3010/api/usage; echo; ! curl -s http://127.0.0.1:3010/api/usage | grep -i 'could not run'",
               "the token panel (no Claude Code sessions exist on this machine)", timeout=120)),
    run("launchctl-load", "", "guide, 'Install it'", printed="launchctl load -w",
        not_testable="only the start of the line the installer prints with your own file's path; the guide says you do not need it, because the installer starts FleetView straight away"),
    run("stop", "python3 install.py --stop", "guide, 'Every command and setting'", ok=[0, 1]),
    {"id": "start-at-login", "kind": "launchd", "wait": 15, "counts": True,
     "what": "the LaunchAgent: switched on and started as your Mac does when you sign in; the page must answer",
     "check": FV_UP + " && sleep 25 && echo 'token panel under launchd:' && curl -s http://127.0.0.1:3010/api/usage",
     "check_tries": 6, "log_glob": "fleetview.log"},
    run("stop-2", "python3 install.py --stop", "guide, 'Every command and setting'", ok=[0, 1]),
    run("start", "python3 install.py --start", "guide, 'Every command and setting'",
        expect=r"FleetView (started|is already running)", check=FV_UP),
    run("stop-3", "python3 install.py --stop", "guide, 'Every command and setting'", ok=[0, 1]),
    run("npm-install", "npm install", "guide, 'See it before your own sessions exist'", timeout=600),
    {"id": "demo", "kind": "serve", "cmd": "npm run demo", "url": "http://localhost:3011/graph.html", "wait": 60,
     "source": "guide, 'See it before your own sessions exist'", "desktop": False, "what": "made-up sessions on 3011",
     "counts": True},
    {"id": "watcher", "kind": "serve", "cmd": "node watcher.js", "url": "http://localhost:3010/graph.html", "wait": 40,
     "source": "guide, 'Every command and setting'", "what": "FleetView in this Terminal window", "counts": True},
    {"id": "npm-start", "kind": "serve", "cmd": "npm start", "url": "http://localhost:3010/graph.html", "wait": 40,
     "source": "guide, 'Every command and setting'", "what": "the same, through npm", "counts": True},
    run("copy", "cp -R outliers-ws-02-fleetview-mac fleetview-test", "guide, 'The safe way', step 1", cwd="~",
        check="test -f ~/fleetview-test/watcher.js"),
    run("cd-copy", "cd fleetview-test", "guide, 'The safe way', step 2", cwd="~", check="test -d ~/fleetview-test"),
    run("rm-pid", "rm -f fleetview.pid", "guide, 'The safe way', step 2", cwd="~/fleetview-test"),
    run("copy-port", "python3 install.py --yes --port 3012", "guide, 'The safe way', step 2", cwd="~/fleetview-test",
        timeout=900, check="grep -q 3012 ~/fleetview-test/config.json"),
    run("copy-start", "python3 install.py --start", "guide, 'The safe way', step 3", cwd="~/fleetview-test",
        check="curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://localhost:3012/graph.html | grep -E '^2'"),
    run("venv", VENV_MAKE, "guide, 'The safe way', step 4", cwd="~", timeout=300),
    run("pip-pytest", VENV_PIP, "guide, 'The safe way', step 4", cwd="~/fleetview-test", timeout=600,
        expect=r"Successfully installed|already satisfied"),
    run("npm-test", "npm test", "guide, 'The safe way', step 4 (in the copy)", cwd="~/fleetview-test", timeout=900,
        expect=NPM_60),
    run("tests", VENV_TEST, "guide, 'The safe way', step 4 (in the copy)", cwd="~/fleetview-test", timeout=1200,
        expect=r"27 passed, 3 skipped"),
    run("copy-stop", "python3 install.py --stop", "guide, 'The safe way', step 5", cwd="~/fleetview-test", ok=[0, 1]),
    {"id": "copy-npm-start", "kind": "serve", "cmd": "PORT=3012 npm start", "url": "http://localhost:3012/graph.html",
     "wait": 40, "cwd": "~/fleetview-test", "source": "guide, 'Fit it to your own AI system'",
     "what": "the copy in a Terminal window, on 3012", "counts": True},
    run("claude", "", "guide, 'Fit it to your own AI system'", printed="claude",
        not_testable="it needs your own Claude Code login, which a test Mac does not have"),
    run("cd-back", "cd ../outliers-ws-02-fleetview-mac", "guide, 'The safe way', step 6", cwd="~/fleetview-test",
        check="test -d ~/outliers-ws-02-fleetview-mac"),
    run("install-yes", "python3 install.py --yes", "guide, 'Every command and setting'", timeout=900, expect=r"config[.]json"),
    run("stop-4", "python3 install.py --stop", "guide, 'Every command and setting'", ok=[0, 1]),
    run("make-demo", "node tools/make-demo.js ~/fleetview-busy-day --sessions 30", "guide, 'Every command and setting'",
        timeout=300, check="test -d ~/fleetview-busy-day"),
    run("other-setup", "", "guide, 'Other tools'", printed="npm run setup",
        not_testable="it is a command of another tool, Claude-Code-Agent-Monitor, which this guide warns against running"),
    run("other-hooks", "", "guide, 'Other tools'", printed="npm run install-hooks",
        not_testable="it is a command of another tool, Claude-Code-Agent-Monitor, which this guide warns against running"),
    run("uninstall", "python3 install.py --uninstall", "guide, 'Every command and setting'", stdin=ENTER,
        expect=r"FleetView uninstall", check="! launchctl list | grep -i fleetview && ! ls ~/Library/LaunchAgents/ | grep -i fleet"),
]}

# ------------------------------------------------------------------ ProjectForge
# Every printed command line of the ProjectForge Mac PDF, inside sentences too (commands/ws-03.json, round 2).
M3 = "outliers-ws-03-projectforge-mac"
PF = "curl -s -o /dev/null -w '%%{http_code}' --max-time 5 http://127.0.0.1:%d | grep -E '^(2|3)'"
PF_UP = PF % 3020
SPECS[M3] = {"steps": prereqs() + [
    fresh_copies(),
    run("python-prefix", 'python3 -c "import sys; print(sys.prefix)"', "guide, 'Before you start on a Mac'", cwd="~",
        what="the guide's Python check; its answer differs with Homebrew (the guide says what each answer means)"),
    run("claude-path", "echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> ~/.zshrc", "guide, 'Before you start on a Mac'", cwd="~"),
    run("claude-version", "claude --version", "guide, 'Before you start'", cwd="~", expect=r"Claude Code"),
    run("python-version", "python3 --version", "guide, 'Before you start'", cwd="~", expect=r"Python 3"),
    run("git-version", "git --version", "guide, 'Before you start'", cwd="~", expect=r"git version"),
    run("venv", VENV_MAKE, "guide, 'Before you start'", cwd="~", timeout=300),
    run("pip-pytest", VENV_PIP, "guide, 'Before you start'", cwd="~", timeout=600,
        expect=r"Successfully installed|already satisfied"),
    clone(M3, "guide, 'Install it', step 2")] + harness_steps(M3) + [
    cd(M3),
    run("install", "python3 install.py", "guide, 'Install it', step 2 (Return for every default, y at 'Go ahead?')",
        stdin=ENTER, timeout=600, expect=r"done:",
        check="test -f data/forge.db && test -f ~/.claude/projectforge/forge_agent.py"),
    {"id": "board", "kind": "serve", "cmd": "python3 forge.py serve", "url": "http://127.0.0.1:3020", "wait": 40,
     "source": "guide, 'Your first day'", "desktop": True, "what": "the web board", "counts": True},
    {"id": "board-3021", "kind": "serve", "cmd": "python3 forge.py serve --port 3021", "url": "http://127.0.0.1:3021", "wait": 40,
     "source": "guide, 'Install it', step 6", "what": "the board on another port", "counts": True},
    run("add-project", "python3 forge.py add-project \"Content week 39\" --dept content --actor you",
        "guide, 'Adding work from the terminal'", expect=r"pf-p-"),
    run("add-task", "", "guide, 'Adding work from the terminal'",
        printed="python3 forge.py add-task pf-p-5baff3 \"Draft 3 posts\" --status ready --agent writer-bot --actor you",
        not_testable="pf-p-5baff3 is an example; you type the project id your own add-project line printed, which was a different code on each test Mac"),
    run("projects", "python3 forge.py projects", "guide, 'Every command and setting'"),
    run("agent-tool", "forge=\"$HOME/.claude/projectforge/forge_agent.py\"\n"
        "python3 $forge open --agent content-lead --dept content --project \"Content week 39\" --title \"Newsletter\" --assignee writer-bot",
        "guide, 'What your agents run' (both lines, in 1 Terminal window)", cwd="~", ok="any",
        expect=r"(?i)refused|opened|card", what="a worker is refused unless a manager was named at install"),
    run("hygiene", "python3 forge.py hygiene", "guide, 'When it goes wrong'"),
    run("mirror", "python3 forge.py mirror", "guide, 'Every command and setting'"),
    {"id": "demo-board", "kind": "serve", "cmd": "python3 tools/demo_board.py --out demo --serve", "url": "http://127.0.0.1:3029",
     "wait": 40, "source": "guide, 'Every command and setting'", "what": "the demo board of made-up work", "counts": True},
    run("run-if-ready", "", "guide, 'Every command and setting'", printed="python3 tools/run_if_ready.py",
        not_testable="it starts Claude when a card is ready, and Claude needs your own Claude Code login"),
    run("schedule-install", "python3 tools/schedule.py --install", "guide, 'The optional schedule'", timeout=120),
    run("schedule-remove", "python3 tools/schedule.py --remove", "guide, 'The optional schedule'", ok=[0, 1]),
    run("start-with-computer", "python3 install.py --start-with-computer", "guide, 'Install it', step 7",
        stdin=ENTER, timeout=300),
    {"id": "board-at-login", "kind": "launchd", "wait": 15, "match": r"ai\.outliers\.projectforge\.plist$", "counts": True,
     "what": "the LaunchAgent that starts the board when you sign in: switched on and started; the board must answer on 3020",
     "check": PF_UP, "check_tries": 12},
    {"id": "board-page-from-login-job", "kind": "shot", "url": "http://127.0.0.1:3020", "wait": 20,
     "what": "the board started by the LaunchAgent"},
    run("launchctl-list", "launchctl list | grep outliers", "guide, 'Before you start on a Mac'", cwd="~",
        expect=r"ai[.]outliers[.]projectforge"),
    run("serve-stop", "python3 forge.py serve --stop", "guide, 'Every command and setting'", ok=[0, 1]),
    run("forge-run-dry", "", "guide, 'Install it', step 10", printed="/forge-run dry",
        not_testable="it is typed inside Claude Code, which needs your own Claude Code login"),
    run("make-copy", "python3 forge.py make-copy ../projectforge-practice", "guide, 'The safe way', step 1",
        timeout=120, expect=r"(?i)practice copy"),
    run("cd-copy", "cd ../projectforge-practice", "guide, 'The safe way', step 2", check="test -d ~/projectforge-practice"),
    {"id": "copy-board", "kind": "serve", "cmd": "python3 forge.py serve", "url": "http://127.0.0.1:3021", "wait": 40,
     "cwd": "~/projectforge-practice", "source": "guide, 'The safe way', step 3", "what": "the practice copy's board, on 3021",
     "counts": True},
    run("tests", VENV_TEST, "guide, 'The safe way', step 4 (in the copy)", cwd="~/projectforge-practice", timeout=1200,
        expect=r"157 passed, 1 skipped"),
    run("cd-back", "cd ../outliers-ws-03-projectforge-mac", "guide, 'The safe way', step 5", cwd="~/projectforge-practice",
        check="test -d ~/outliers-ws-03-projectforge-mac"),
    run("claude", "", "guide, 'Fit it to your own AI system'", printed="claude",
        not_testable="it opens Claude Code, which needs your own Claude Code login"),
    run("claude-p", "", "guide, 'How it was built'", printed="claude -p",
        not_testable="it only names how Ashley's old timer started Claude, and is not a line to type"),
    run("claude-p-forge-run", "", "guide, 'The optional schedule'", printed='claude -p "/forge-run"',
        not_testable="the guide tells you never to put this line on a timer; it also needs your own Claude Code login"),
    run("uninstall", "python3 install.py --uninstall", "guide, 'What the installer does'", stdin="y\n" + ENTER, ok=[0],
        check="test ! -f ~/.claude/projectforge/forge_agent.py"),
]}

# ------------------------------------------------------------------ Jeeves
# Every printed command line of the Jeeves Mac PDF, inside sentences too (commands/ws-04.json, round 2).
M4 = "outliers-ws-04-jeeves-mac"
JV = "curl -s --max-time 5 http://127.0.0.1:%d/api/health"


def jeeves_serve(id_, cmd, port, source, **kw):
    d = {"id": id_, "kind": "serve", "cmd": cmd, "url": "http://127.0.0.1:%d/" % port, "wait": 45,
         "source": source, "what": "Jeeves on %d" % port, "counts": True, "check": JV % port}
    d.update(kw)
    return d


SPECS[M4] = {"steps": prereqs() + [
    fresh_copies(),
    run("python-prefix", 'python3 -c "import sys; print(sys.prefix)"', "guide, 'Before you start on a Mac'", cwd="~",
        what="the guide's Python check; its answer differs with Homebrew (the guide says what each answer means)"),
    run("node-version", "node --version", "guide, 'What you need'", cwd="~", expect=r"^v(2[2-9]|[3-9][0-9])[.]"),
    run("claude-path", "echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> ~/.zshrc", "guide, 'Before you start on a Mac'", cwd="~"),
    run("claude-version", "claude --version", "guide, 'What you need'", cwd="~", expect=r"Claude Code"),
    run("python-version", "python3 --version", "guide, 'What you need'", cwd="~", expect=r"Python 3"),
    run("git-version", "git --version", "guide, 'What you need'", cwd="~", expect=r"git version"),
    run("ccusage-install", "npm install -g --prefix ~/.local ccusage", "guide, 'What you need'", cwd="~", timeout=600,
        expect=r"added [0-9]+ package"),
    run("ccusage-version", "ccusage --version", "guide, 'What you need'", cwd="~", expect=r"[0-9]+[.][0-9]+"),
    run("ccusage-plain", "", "guide, 'What you need'", printed="npm install -g ccusage",
        not_testable="the guide prints it only to say a Mac refuses it; it was left out of this test, and a separate test-Mac run on 2026-09-25 (https://github.com/OUTLIERS-ai/outliers-mac-test/actions/runs/36154211225) got \"EACCES: permission denied\""),
    clone(M4, "guide, 'Install it', step 2")] + harness_steps(M4) + [
    cd(M4),
    run("install", "python3 install.py", "guide, 'Install it', step 3 (Return for each default)", stdin=ENTER, timeout=600,
        expect=r"Wrote config[.]json|Nothing changed", check="test -f config.json && cat config.json"),
    jeeves_serve("jeeves-page", "python3 start.py", 4040, "guide, 'Install it', step 8", desktop=True),
    run("stop", "python3 start.py --stop", "guide, 'Stopping it'", expect=r"Stopped Jeeves|not running"),
    jeeves_serve("no-open", "python3 start.py --no-open", 4040, "guide, 'Every command and setting'"),
    run("stop-2", "python3 start.py --stop", "guide, 'Stopping it'", expect=r"Stopped Jeeves|not running"),
    {"id": "demo-page", "kind": "serve", "cmd": "python3 tools/demo.py ../jeeves-demo --serve --port 4099",
     "url": "http://127.0.0.1:4099/", "wait": 60, "source": "guide, 'Try it on made-up data first'",
     "what": "Sam the bookkeeper", "counts": True},
    run("install-yes", "python3 install.py --yes", "guide, 'Every command and setting'", timeout=300),
    run("launcher", "python3 install.py --launcher --yes", "guide, 'Every command and setting'", stdin=ENTER, timeout=300,
        expect=r"LaunchAgents/ai[.]outliers[.]jeeves[.]plist"),
    {"id": "start-at-login", "kind": "launchd", "wait": 15, "counts": True,
     "what": "the LaunchAgent: switched on and started as your Mac does when you sign in; Jeeves must answer on 4040",
     "check": JV % 4040, "check_tries": 12},
    run("launchctl-list", "launchctl list | grep outliers", "guide, 'Every command and setting'", cwd="~",
        expect=r"ai[.]outliers[.]jeeves"),
    run("stop-3", "python3 start.py --stop", "guide, 'Stopping it'", expect=r"Stopped Jeeves|not running"),
    run("copy", "python3 install.py --copy ../jeeves-trial", "guide, 'The safe way to change it'", timeout=300,
        expect=r"Made a copy of Jeeves to experiment on"),
    run("cd-copy", "cd ../jeeves-trial", "guide, 'The safe way to change it'", check="test -d ~/jeeves-trial"),
    run("venv", VENV_MAKE, "guide, 'The safe way to change it'", cwd="~", timeout=300),
    run("pip-pytest", VENV_PIP, "guide, 'The safe way to change it'", cwd="~", timeout=600,
        expect=r"Successfully installed|already satisfied"),
    run("tests", VENV_TEST, "guide, 'The safe way to change it' (in the copy)", cwd="~/jeeves-trial", timeout=1200,
        expect=r"64 passed, 13 skipped"),
    run("cd-copy-home", "cd jeeves-trial", "guide, 'Fit it to your own AI system'", cwd="~", check="test -d ~/jeeves-trial"),
    run("claude", "", "guide, 'Fit it to your own AI system'", printed="claude",
        not_testable="it opens Claude Code, which needs your own Claude Code login"),
    run("port-install", "python3 install.py --port 4041", "guide, 'When it goes wrong'", stdin=ENTER, timeout=300),
    jeeves_serve("port-start", "python3 start.py --port 4041", 4041, "guide, 'When it goes wrong'"),
    run("stop-4", "python3 start.py --stop", "guide, 'Stopping it'", expect=r"Stopped Jeeves|not running"),
    run("folders", "", "guide, 'Every command and setting'", printed="python3 install.py --vault <folder> --crm <folder> --agents <folder>",
        not_testable="it is a pattern, not a line to type as printed: you type your own folders where each <folder> is"),
    run("config", "", "guide, 'Every command and setting'", printed="python3 start.py --config <file>",
        not_testable="it is a pattern, not a line to type as printed: you type your own settings file where <file> is"),
    run("cd-crm", "cd ~/CRM", "guide, 'Today'", cwd="~", check="test -d ~/CRM"),
    run("today", "", "guide, 'Today'", printed="python3 _engine/today.py --write",
        not_testable="it runs inside your CRM folder and only once your CRM has the program _engine/today.py, which builds your daily Today.md list and comes with a later CRM session; the test Macs' CRM came from the first CRM session and does not have it"),
    run("word-git-clone", "", "guide, history", printed="git clone",
        not_testable="the word table names the command only; the full line, which was run, is under Install it"),
    run("word-claude-p", "", "guide, history", printed="claude -p",
        not_testable="the name of the way Jeeves calls Claude Code, inside a sentence of the history, not a line to type"),
    run("chat-echo", "", "guide, 'Chat'", printed="echo hello",
        not_testable="part of a message typed into Jeeves's chat in a test on Ashley's own PC, not a Terminal line"),
    run("word-venv", "", "guide, 'The safe way to change it'", printed="python3 -m venv",
        not_testable="the start of the line python3 -m venv ~/outliers-checks, named in the sentence that explains it"),
    run("uninstall", "python3 install.py --uninstall", "guide, 'Every command and setting'", stdin=ENTER,
        expect=r"removed", check="! launchctl list | grep -i jeeves && ! ls ~/Library/LaunchAgents/ | grep -i jeeves"),
]}


# ================================================================== Session 5 and Fathom (wave s8s5)
# The Mac PDFs of The Critic, Drawing With A Program and The Meeting Agent, and the Mac READMEs,
# 2026-09-25. Every printed line, in the order the Mac PDF or README prints it.

def fresh_s5():
    """Harness only: what an earlier member test on the same Mac left (Homebrew order A, then B)
    and the setup script does not move (it moves only ~/outliers-*), moved aside."""
    return check("fresh-copies", "mkdir -p /tmp/earlier-copies; for d in ~/fathom-meeting-agent-mac ~/.claude/agents; do "
                 "[ -e \"$d\" ] && mv \"$d\" /tmp/earlier-copies/$(basename \"$d\")-$$; done; true",
                 "harness only: move aside copies an earlier member test on this Mac left", cwd="~")


# ------------------------------------------------------------------ The Critic
M5 = "outliers-critic-mac"
SPECS[M5] = {"steps": [
    fresh_s5(),
    clone(M5, "guide, part 1 'Where'")] + harness_steps(M5) + [
    check("no-backslash-paths", r"! grep -n '[\\]' the-critic.md && echo 'no backslash in any folder path'",
          "harness only: the agent file writes every folder path with /, which a Mac reads as a folder"),
    # wave s8s5 second round: grep piped into head exited 0 with nothing found (the file writes the name
    # with capitals). grep alone exits 1 when nothing matches, so this check can no longer pass unseen.
    check("canon-named", "grep -n -i 'design-critique-canon' the-critic.md",
          "harness only: the agent file names the canon (in any capitals), and where it looks for it"),
    run("mkdir-agents", "mkdir -p ~/.claude/agents", "guide, part 1 'Where'", cwd="~",
        check="test -d ~/.claude/agents"),
    run("copy-into-agents", "cp outliers-critic-mac/the-critic.md outliers-critic-mac/design-critique-canon.md ~/.claude/agents/",
        "guide, part 1 'Where'", cwd="~",
        check="ls -la ~/.claude/agents && test -f ~/.claude/agents/the-critic.md && test -f ~/.claude/agents/design-critique-canon.md"),
    run("claude-edit", "", "guide, part 1 'Where' (the prompt that changes the canon's place)", printed="claude",
        not_testable="it opens Claude Code to make the change, which needs your own Claude Code login"),
]}

# ------------------------------------------------------------------ Drawing With A Program
M6 = "outliers-diagrams-mac"
DG = "source ~/outliers-diagrams-python/bin/activate && "
SPECS[M6] = {"steps": [
    fresh_s5(),
    run("python-prefix", 'python3 -c "import sys; print(sys.prefix)"', "guide, 'Before you start on a Mac'", cwd="~",
        what="the guide's Python check; its answer differs with Homebrew (the guide says what each answer means)"),
    clone(M6, "guide, 'Making it yours' (the address), and the box")] + harness_steps(M6) + [
    cd(M6),
    run("venv", "python3 -m venv ~/outliers-diagrams-python", "README, 'Running it'", timeout=300),
    run("pip", DG + "python -m pip install pillow playwright", "README, 'Running it'", timeout=900,
        expect=r"Successfully installed|already satisfied"),
    run("chromium", DG + "python -m playwright install chromium", "README, 'Running it'", timeout=900),
    run("make-diagrams", DG + "python make_diagrams.py", "README, 'Running it'", timeout=600,
        check="n=$(ls png/*.png | wc -l | tr -d ' '); echo \"$n pictures in png/\"; test \"$n\" -ge 10 "
              "&& mkdir -p \"$OUT/shots\" && cp png/*.png \"$OUT/shots/\""),
    run("cd-labs", "cd labs", "labs/README.md, 'Running any of them'", check="test -d ~/%s/labs" % M6),
    run("lab-ten", DG + "python ten_design_systems.py", "labs/README.md, 'Running any of them'", cwd="{repo}/labs",
        timeout=600),
    run("lab-colour", DG + "python colour_measure.py", "labs/README.md, 'Running any of them'", cwd="{repo}/labs",
        timeout=300),
    check("lab-phone", DG + "python phone_width.py", "harness only: another lab, in the same private folder",
          cwd="{repo}/labs", timeout=300),
    check("lab-background", DG + "python what_a_background_is_for.py", "harness only: another lab, in the same private folder",
          cwd="{repo}/labs", timeout=300),
]}

# ------------------------------------------------------------------ The Meeting Agent (Fathom)
M7 = "fathom-meeting-agent-mac"
FA = "source .venv/bin/activate && "
FA_OPEN = FA + "python -m playwright open --user-data-dir=.browser-profile https://fathom.video"


def fathom_clone():
    printed = "git clone %s%s.git" % (GH, M7)
    if FROM_MAIN:
        return {"id": "clone", "kind": "run", "counts": True, "source": "guide, step 2",
                "what": "EXPLORATORY: the main repo cloned into the -mac folder name (no -mac repo yet)",
                "printed": printed, "cmd": "git clone %sfathom-meeting-agent.git %s" % (GH, M7), "cwd": "~",
                "check": "test -d ~/%s" % M7, "no_auto_retry": True}
    return {"id": "clone", "kind": "run", "counts": True, "source": "guide, step 2", "what": "copy the repo down",
            "cmd": printed, "cwd": "~", "check": "test -d ~/%s" % M7, "no_auto_retry": True}


SPECS[M7] = {"steps": [W.claude_code_prereq(), fresh_s5(),
    run("python-prefix", 'python3 -c "import sys; print(sys.prefix)"', "guide, 'Before you start on a Mac'", cwd="~",
        what="the guide's Python check; its answer differs with Homebrew (the guide says what each answer means)"),
    run("claude-path", "echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> ~/.zshrc", "guide, 'Before you start on a Mac'", cwd="~"),
    run("claude-version", "claude --version", "guide, 'Before you start on a Mac'", cwd="~", expect=r"Claude Code"),
    fathom_clone()] + harness_steps(M7) + [
    cd(M7),
    run("cd-zip", "", "guide, step 3 (zip route)", printed="cd ~/Downloads/fathom-meeting-agent-mac-main",
        not_testable="it is only for the zip route, which was not tried on the test Macs"),
    run("venv", "python3 -m venv .venv", "guide, step 3", timeout=300),
    run("pip", FA + "python -m pip install playwright", "guide, step 3", timeout=900,
        expect=r"Successfully installed|already satisfied"),
    run("chromium", FA + "python -m playwright install chromium", "guide, step 3", timeout=900),
    run("open-fathom", "", "guide, step 4", printed=FA_OPEN,
        not_testable="it needs you to log into Fathom by hand; see the next page"),
    check("open-blank", FA + "python -m playwright open --user-data-dir=.browser-profile about:blank > \"$OUT/open-blank.log\" 2>&1 & "
          "p=$!; for i in $(seq 1 40); do [ -d .browser-profile ] && break; sleep 1; done; sleep 3; "
          "pkill -f 'user-data-dir=.browser-profile' ; kill $p 2>/dev/null; sleep 1; "
          "test -d .browser-profile && echo 'the browser opened and made the .browser-profile folder'",
          "harness only: the step 4 line with a blank page in place of Fathom's address (Fathom is never contacted)",
          timeout=120),
    run("claude-step5", "", "guide, step 5", printed="claude",
        not_testable="it opens Claude Code, which needs your own Claude Code login"),
    check("agent-python", ".venv/bin/python -c \"import playwright; print('Playwright found by .venv/bin/python')\"",
          "harness only: the Python the agent file tells Claude to use on a Mac finds Playwright"),
]}



# ================================================================== Session 2 (wave s2, 2026-09-26)
# The Mac PDFs of the 4 Gather layers with code (1, 2, 4, 5) and the Seven Ratings sheet, and their Mac
# READMEs. Every printed line, in the order the Mac PDF prints it, plus the README lines named below.
# On a Mac, Gather keeps Playwright in 1 private Python folder, ~/outliers-gather-python, made in
# Layer 1 (and again in Layer 4, which stands on its own): a Mac whose `python3` is Homebrew's refuses a
# plain `python3 -m pip install` (wave 0a M4). Every Gather command box on a Mac starts with the line
# that switches the Terminal window into that folder; a step prints that line and the command after it,
# and runs both in 1 Terminal window, as a member types them (the ProjectForge 'agent-tool' shape).

GP = "~/outliers-gather-python"
GACT = "source ~/outliers-gather-python/bin/activate"
ENGINE = "~/CRM/_engine"


def gstep(id_, line, source, cwd=ENGINE, **kw):
    """A Gather line typed in a Terminal window switched into the private folder: both lines, 1 window."""
    return run(id_, GACT + "\n" + line, source, cwd=cwd, **kw)


def fresh_gather():
    """Harness only: Playwright's browser folder left by an earlier member test on the same Mac
    (Homebrew order A, then B) is moved aside, so each order downloads the browser as a new member
    does. The setup script already moves ~/outliers-*, ~/CRM and ~/.outliers-* (homebrew.sh B)."""
    return check("fresh-copies", "mkdir -p /tmp/earlier-copies; for d in ~/Library/Caches/ms-playwright; do "
                 "[ -e \"$d\" ] && mv \"$d\" /tmp/earlier-copies/$(basename \"$d\")-$$; done; true",
                 "harness only: move aside the browser an earlier member test on this Mac downloaded", cwd="~")


def gather_python_prereq():
    """The private folder Layer 1 makes, with Playwright and its browser in it (not counted: the Layer 1
    member test runs these lines as printed)."""
    return {"id": "prereq-gather-python", "kind": "prereq", "counts": False,
            "what": "the Gather private Python folder, made as Layer 1 prints it (not scored here)",
            "cmd": "python3 -m venv ~/outliers-gather-python && " + GACT + " && python3 -m pip install playwright "
                   "&& python3 -m playwright install chromium",
            "cwd": "~", "no_auto_retry": True, "timeout": 1200}


def gather_folder_steps(source):
    """The Python check, then the lines that make the private folder and put Playwright and its browser in it."""
    return [
        run("python-prefix", 'python3 -c "import sys; print(sys.prefix)"', "guide, 'Before you start on a Mac'", cwd="~",
            what="the guide's Python check; its answer differs with Homebrew (the guide says what each answer means)"),
        run("venv", "python3 -m venv " + GP, source, cwd="~", timeout=300, check="test -x " + GP + "/bin/python3"),
        gstep("pip", "python3 -m pip install playwright", source, cwd="~", timeout=900,
              expect=r"Successfully installed|already satisfied"),
        gstep("chromium", "python3 -m playwright install chromium", source, cwd="~", timeout=1200),
        check("sizes", "du -sk " + GP + "/lib/python3*/site-packages/playwright ~/Library/Caches/ms-playwright/* "
              "&& du -sk ~/Library/Caches/ms-playwright",
              "harness only: the size of Playwright in the private folder and of the browser in its own folder "
              "(for the guide's 'About ... MB in all')", cwd="~"),
    ]


def gather_install(mac, expect_file, source="guide, 'Build it'"):
    return [clone(mac, source)] + harness_steps(mac) + [
        cd(mac),
        gstep("install", "python3 install.py", source + " (Return for every answer it offers)", cwd="{repo}",
              stdin=ENTER, timeout=600, refuse=r"ONE MORE STEP", check="test -f %s/%s" % (ENGINE, expect_file)),
    ]


def cd_engine(source):
    return run("cd-engine", "cd " + ENGINE, source, cwd="~", check="test -d " + ENGINE)


def login_opens(line, what):
    """Harness only: the sign-in line opens its browser window from the private folder. The harness
    photographs the screen, then presses Return; nobody signs in, so no site is ever logged into."""
    return {"id": "login-opens", "kind": "interactive", "counts": False, "cwd": ENGINE, "wait": 40,
            "cmd": GACT + "\n" + line, "what": what}


# ------------------------------------------------------------------ Gather Layer 1: The Doorman
M8 = "outliers-gather-01-foundation-mac"
SPECS[M8] = {"steps": W.crm_prereqs(6) + [fresh_gather()] + gather_folder_steps("guide, 'Before you start on a Mac'") + [
    run("python-version", "python3 --version", "README, 'Before you start'", cwd="~", expect=r"^Python 3[.]"),
    ] + gather_install(M8, "gather.py") + [
    run("tests", "python3 tests/test_doorman.py", "README, 'The tests are the proof'", timeout=600,
        expect=r"all checks passed"),
    cd_engine("guide, 'Now use it'"),
    gstep("status", "python3 gather.py status", "guide, 'Now use it'", expect=r"(?i)blocked"),
    login_opens("python3 gather.py login", "harness only: the LinkedIn sign-in line opens its own browser window "
                "(photographed); Return is pressed and nobody signs in"),
    run("login", "", "guide, 'Now use it'", printed="python3 gather.py login",
        not_testable="it needs you to sign in to LinkedIn by hand, with your own account"),
    run("tests-crm", "", "README, 'The tests are the proof'",
        printed="OUTLIERS_CRM=/path/to/your/CRM python3 tests/test_doorman.py",
        not_testable="you type your own CRM folder where /path/to/your/CRM is"),
    run("claude", "", "guide, 'Give this to your assistant'", printed="claude",
        not_testable="it opens Claude Code, which needs your own Claude Code login"),
]}

# ------------------------------------------------------------------ Gather Layer 2: Going and Looking
M9 = "outliers-gather-02-basics-mac"
MADE_UP = ("printf 'First Name,Last Name,URL,Email Address,Company,Position,Connected On\\n"
           "Sam,Testperson,https://www.linkedin.com/in/sam-testperson-000,,Made Up Ltd,Owner,01 Sep 2026\\n' > %s/Connections.csv"
           " && cat %s/Connections.csv" % (ENGINE, ENGINE))
SPECS[M9] = {"steps": W.crm_prereqs(6) + [W.prereq("outliers-gather-01-foundation"), gather_python_prereq(),
                                           fresh_gather()] + gather_install(M9, "gather_find.py") + [
    run("tests", "python3 tests/test_jobs.py", "README, 'The tests are the proof'", timeout=600,
        expect=r"all checks passed"),
    cd_engine("guide, 'Now use it'"),
    check("made-up-export", MADE_UP, "harness only: a 1-row made-up LinkedIn export saved into the _engine folder, "
          "as the guide says to save yours", cwd=ENGINE),
    gstep("find-export", "python3 gather.py find export Connections.csv", "guide, 'Now use it'", timeout=300),
    # wave s2 readers: the guide says "add --commit to the same line"; the line is printed and run on the made-up file
    gstep("find-export-commit", "python3 gather.py find export Connections.csv --commit", "guide, 'Now use it'",
          timeout=300, check="grep -rl -i 'testperson' ~/CRM --include=*.jsonl --include=*.md | head -3 | grep ."),
    run("undo-probe", "", "guide, 'Now use it'", printed="python3 gather.py undo --probe",
        not_testable="it opens LinkedIn, which needs you to sign in by hand with your own account (Layer 1)"),
    run("claude", "", "guide, 'Give this to your assistant'", printed="claude",
        not_testable="it opens Claude Code, which needs your own Claude Code login"),
]}

# ------------------------------------------------------------------ Gather Layer 4: The Same Shape
M10 = "outliers-gather-04-facebook-mac"
FB_NOT = "it needs you to sign in to Facebook by hand, with your own account"
SPECS[M10] = {"steps": W.crm_prereqs(6) + [fresh_gather()] + gather_folder_steps("guide, 'Before you start on a Mac'")
              + gather_install(M10, "facebook.py") + [
    run("tests", "python3 tests/test_governor.py", "README, 'The tests are the proof'", timeout=600,
        expect=r"all checks passed"),
    cd_engine("guide, 'Prove it, in this order'"),
    gstep("status", "python3 facebook.py status", "README, 'Use it'", expect=r"(?i)blocked"),
    login_opens("python3 facebook.py login", "harness only: the Facebook sign-in line opens its own browser window "
                "(photographed); Return is pressed and nobody signs in"),
    run("login", "", "guide, 'Prove it', step 1", printed="python3 facebook.py login", not_testable=FB_NOT),
    run("probe", "", "guide, 'Prove it', step 2", printed="python3 facebook.py probe",
        not_testable="it opens your Facebook home page, which needs your own Facebook sign-in first"),
    run("find-query", "", "guide, 'Prove it', step 3", printed='python3 facebook.py find-groups --query "your words here"',
        not_testable="it searches Facebook, which needs your own Facebook sign-in first"),
    run("find-groups", "", "guide, 'Once it is proven'", printed="python3 facebook.py find-groups",
        not_testable="it searches Facebook, which needs your own Facebook sign-in first"),
    run("join-commit", "", "guide, 'Once it is proven'", printed="python3 facebook.py join --commit",
        not_testable="it asks to join groups on Facebook, which needs your own Facebook sign-in and your own list"),
    run("claude", "", "guide, 'Give this to your assistant'", printed="claude",
        not_testable="it opens Claude Code, which needs your own Claude Code login"),
]}

# ------------------------------------------------------------------ Gather Layer 5: When You Are Not There
M11 = "outliers-gather-05-timetable-mac"
TT_PLIST = "~/Library/LaunchAgents/com.outliers.gather.timetable.plist"
SPECS[M11] = {"steps": W.crm_prereqs(6) + [W.prereq("outliers-gather-01-foundation"), W.prereq("outliers-gather-02-basics"),
                                           gather_python_prereq(), fresh_gather()] + gather_install(
        M11, "timetable.py", "guide, 'Build it'") + [
    {"id": "start-at-login", "kind": "launchd", "cwd": ENGINE, "wait": 15, "counts": True,
     "match": r"com[.]outliers[.]gather[.]timetable[.]plist$",
     "what": "the LaunchAgent the installer writes: switched on and started as your Mac does when you sign in; "
             "the timetable must report itself running",
     "check": "python3 timetable.py status", "check_tries": 6, "log_glob": "../_state/timetable/*.log"},
    check("timetable-python", "p=$(plutil -extract ProgramArguments.0 raw -o - " + TT_PLIST + "); echo \"the LaunchAgent starts: $p\"; "
          "case \"$p\" in \"$HOME/outliers-gather-python/bin/\"*) ;; *) echo 'not the private folder'; exit 1;; esac; "
          "\"$p\" -c \"import playwright; print('that Python finds Playwright, so the jobs it starts can open the browser')\"",
          "harness only: the LaunchAgent starts the timetable with the private folder's Python, which finds Playwright"),
    run("tests", "python3 tests/test_timetable.py", "README, 'The tests are the proof'", timeout=600,
        expect=r"all checks passed"),
    cd_engine("guide, 'Now use it'"),
    gstep("add", 'python3 timetable.py add "python3 gather.py undo" --at 09:30 --days mon,wed,fri', "guide, 'Now use it'"),
    gstep("dry-run", "python3 timetable.py run --dry-run", "guide, 'Now use it'", expect=r"[0-9]{2}:[0-9]{2}"),
    gstep("add-minutes", 'python3 timetable.py add "python3 gather.py undo" --at 09:30 --days mon,wed,fri --minutes 20',
          "guide, 'Now use it'"),
    gstep("start", "python3 timetable.py start", "guide, 'Now use it' (in a sentence)", timeout=120),
    gstep("status", "python3 timetable.py status", "guide, 'How it works' (in a sentence)", ok=[0, 1]),
    gstep("stop", "python3 timetable.py stop", "README, 'Use it'", ok=[0, 1]),
    gstep("install-startup", "python3 timetable.py install-startup", "guide, 'Build it' (in a sentence)",
          timeout=120, expect=r"Installed"),
    # wave s2 readers: the example job needs Layers 1 and 2; with both installed, its line is run as the member would
    gstep("example-job", "python3 gather.py undo", "guide, 'Your CRM' (the example job)", ok="any",
          expect=r"(?i)switched off|blocked"),
    run("claude", "", "guide, 'Give this to your assistant'", printed="claude",
        not_testable="it opens Claude Code, which needs your own Claude Code login"),
]}

# ------------------------------------------------------------------ The Seven Ratings
M12 = "outliers-seven-ratings-mac"
CLAUDE_OWN = "it needs your own Claude Code login, on a paid plan"
SPECS[M12] = {"steps": [
    run("git-version", "git --version", "sheet, step 2", cwd="~", expect=r"^git version"),
    run("install-claude", "curl -fsSL https://claude.ai/install.sh | bash", "sheet, step 3", cwd="~", timeout=600),
    run("claude-path", "echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> ~/.zshrc", "sheet, step 3", cwd="~"),
    run("claude-version", "claude --version", "sheet, step 3", cwd="~", expect=r"[0-9]+[.][0-9]+"),
    run("claude-login", "", "sheet, step 4", printed="claude", not_testable=CLAUDE_OWN),
    run("exit", "", "sheet, step 4 (in a sentence)", printed="/exit",
        not_testable="it is typed inside Claude Code, after you have logged in"),
    run("cd-home", "cd ~", "sheet, step 5", cwd="~", check="test -d ~"),
    dict(clone(M12, "sheet, step 5"), **({"printed": "git clone %s%s.git" % (GH, M12),
                                          "cmd": "git clone %s%s.git %s" % (GH, M12[:-4], M12)} if FROM_MAIN
                                         else {"cmd": "git clone %s%s.git" % (GH, M12)})),
    ] + harness_steps(M12) + [
    cd(M12),
    run("ls", "ls", "sheet, 'If it goes wrong' (in a sentence)", expect=r"SEND-AI-Working-Assessment[.]md"),
    run("add-dir", "", "sheet, step 6", printed="claude --add-dir ~", not_testable=CLAUDE_OWN),
    run("add-dir-inside", "", "sheet, step 6 (in a sentence)", printed="/add-dir",
        not_testable="it is typed inside Claude Code, after you have logged in"),
    run("prompt", "", "sheet, step 7",
        printed="Read `SEND-AI-Working-Assessment.md` and assess my whole system against it. Follow the instructions "
                "in the section headed *For the machine doing the reading*.",
        not_testable="it is typed into Claude Code, which needs your own Claude Code login"),
]}


def get(repo):
    return SPECS[repo]
