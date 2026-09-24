"""What a Mac member would do with each Outliers repo, step by step, as its README or guide prints it.

Every "cmd" is copied from the repo's own words (the "source" field says where). The harness
runs it exactly like that first, then tries the obvious Mac substitute. Steps a member cannot
do on a public test machine (anything needing their own Claude, LinkedIn, Facebook or Fathom
login) are listed with "not_testable" so the gap is visible rather than silently skipped.

Repos checked against GitHub on 2026-09-24. `outliers-content-engine` is PRIVATE and is not
tested here: a public repo's workflow cannot clone it without a secret, and this repo holds none.
"""

GH = "https://github.com/OUTLIERS-ai/"
VAULT = "~/Documents/Second Brain"
CRM = "~/CRM"
ENTER = "\n" * 60
CLAUDE_NOT_TESTABLE = "needs Claude Code logged in to a paid plan: not testable on a public runner"


def clone(repo, counts=True, source="README, Install"):
    return {"id": "clone", "kind": "run" if counts else "prereq", "counts": counts,
            "what": "copy the repo down", "source": source,
            "cmd": "git clone %s%s" % (GH, repo), "cwd": "~", "check": "test -d ~/%s" % repo,
            "no_auto_retry": True}


def prereq(repo, install_cmd="python3 install.py", stdin=ENTER, extra=""):
    """An earlier part the member would already have installed. Done with python3, not scored."""
    return {"id": "prereq-%s" % repo, "kind": "prereq", "counts": False,
            "what": "earlier part, installed first with python3 (not scored here)",
            "cmd": "rm -rf ~/%s && git clone -q %s%s ~/%s && cd ~/%s && %s%s"
                   % (repo, GH, repo, repo, repo, install_cmd, extra),
            "cwd": "~", "stdin": stdin, "no_auto_retry": True, "timeout": 900}


def claude_code_prereq():
    return {"id": "prereq-claude-code", "kind": "prereq", "counts": False,
            "what": "Claude Code installed with Anthropic's Mac installer (never logged in)",
            "cmd": "curl -fsSL https://claude.ai/install.sh | bash && ~/.local/bin/claude --version",
            "cwd": "~", "no_auto_retry": True, "timeout": 600}


def run(id_, cmd, source, cwd="{repo}", what="", **kw):
    d = {"id": id_, "kind": kw.pop("kind", "run"), "cmd": cmd, "source": source, "cwd": cwd, "what": what}
    d.update(kw)
    return d


def check(id_, cmd, what, cwd="{repo}", **kw):
    d = {"id": id_, "kind": "check", "cmd": cmd, "what": what, "cwd": cwd}
    d.update(kw)
    return d


def nul_check():
    return check("no-stray-nul-file",
                 "ls -la; test ! -e nul",
                 "Windows-only '>nul' in the installer would leave a file called 'nul' behind on a Mac")


CRM_LAYERS = ["outliers-crm-01-foundation", "outliers-crm-02-rules", "outliers-crm-03-records",
              "outliers-crm-04-capture", "outliers-crm-05-judgement", "outliers-crm-06-safety",
              "outliers-crm-07-today", "outliers-crm-08-verification"]
SB_PARTS = ["outliers-sb-01-memory", "outliers-sb-02-standards", "outliers-sb-03-capture",
            "outliers-sb-04-operations"]


def crm_prereqs(upto):
    return [prereq(r) for r in CRM_LAYERS[:upto]]


def crm_install(repo, source="README, Install"):
    return [clone(repo),
            run("install", "python install.py", source, stdin=ENTER,
                what="installer, pressing Enter for every default",
                check="test -f ~/CRM/_layers/config.json && python3 -c \"import json,os;"
                      "print(json.load(open(os.path.expanduser('~/CRM/_layers/config.json'))).get('layer'))\"")]


def tests(cmds, source, cwd="{repo}"):
    return [run("test-%d" % (i + 1), c, source, cwd=cwd, what="the repo's own tests", timeout=900)
            for i, c in enumerate(cmds)]


SPECS = {}

# ============================================================== Second Brain set (Session 0)
SPECS["outliers-sb-01-memory"] = {"steps": [
    clone("outliers-sb-01-memory"),
    run("install", "python install.py", "README, 'What this does about it'", stdin=ENTER,
        what="3 questions, Enter for each default",
        check="test -f \"$HOME/Documents/Second Brain/CLAUDE.md\" && test -f \"$HOME/Documents/Second Brain/_layers/config.json\" "
              "&& git -C \"$HOME/Documents/Second Brain\" log --oneline -1"),
    check("vault-readable", "ls -la \"$HOME/Documents/Second Brain\"; tail -20 ~/.claude/CLAUDE.md && grep -q 'Second Brain' ~/.claude/CLAUDE.md",
          "the folder, its history and the pointer in ~/.claude/CLAUDE.md are there"),
    run("claude-reads-it", "", "PDF: 'open Claude Code, drag this PDF in'",
        not_testable=CLAUDE_NOT_TESTABLE + " (the promise 'it tells you something a fresh chat could not')"),
]}

SPECS["outliers-sb-02-standards"] = {"steps": [
    prereq("outliers-sb-01-memory"),
    clone("outliers-sb-02-standards"),
    run("install", "python install.py", "README, 'What this does about it'", stdin=ENTER,
        check="test -f \"$HOME/Documents/Second Brain/_engine/doctor.py\""),
    run("doctor", "python _engine/doctor.py", "README, 'Then:'", cwd=VAULT, ok=[0, 1]),
    run("repair", "python _engine/repair.py", "README, 'Then:'", cwd=VAULT, ok=[0, 1]),
    run("repair-apply", "python _engine/repair.py --apply", "README, 'Then:'", cwd=VAULT, ok=[0, 1]),
] + tests(["python tests/test_check_does_not_cry_wolf.py", "python tests/test_repair_only_when_certain.py"],
          "README names tests/ but prints no command; this is the obvious one")}

SPECS["outliers-sb-03-capture"] = {"steps": [
    prereq("outliers-sb-01-memory"), prereq("outliers-sb-02-standards"),
    clone("outliers-sb-03-capture"),
    run("install", "python install.py", "README, 'What this does about it'", stdin=ENTER,
        check="ls \"$HOME/Documents/Second Brain/.claude/agents\" && test -f \"$HOME/Documents/Second Brain/.claude/skills/youtube-to-notes/SKILL.md\""),
    run("youtube-to-notes", "python \".claude/skills/youtube-to-notes/scripts/youtube_words.py\" \"https://www.youtube.com/watch?v=jNQXAC9IVRw\"",
        "youtube-to-notes/SKILL.md step 1 (Claude runs it; SKILL.md says use python3 on a Mac)", cwd=VAULT,
        what="the YouTube helper on a 19-second public video; expect it to ask for yt-dlp first",
        expect=r"saved|already here", ok="any", timeout=300,
        then_subs=["python3 -m pip install yt-dlp; python3 \".claude/skills/youtube-to-notes/scripts/youtube_words.py\" \"https://www.youtube.com/watch?v=jNQXAC9IVRw\"",
                   "brew install yt-dlp && python3 \".claude/skills/youtube-to-notes/scripts/youtube_words.py\" \"https://www.youtube.com/watch?v=jNQXAC9IVRw\""]),
    run("claude-capture", "", "README: '/capture' and the six assistants",
        not_testable=CLAUDE_NOT_TESTABLE),
] + tests(["python tests/test_youtube_words.py"], "README prints no test command; tests/ holds one file")}

def cron_test(fixed):
    """Put the crontab line the installer printed into the real cron, due 2 minutes from now,
    wrapped only so its output (errors included) lands in a file. `fixed` = the obvious Mac
    repair: quote the folder name (it has a space) and say python3."""
    log = "/tmp/cron-today-%s.log" % ("fixed" if fixed else "printed")
    fix = (" LINE=$(echo \"$LINE\" | sed -E 's#^cd (.*) && python #cd \"\\1\" \\&\\& python3 #'); "
           "echo \"line after the Mac repair: $LINE\"; ") if fixed else ""
    return ("rm -f %s /tmp/cron-alive.log; H=$(date +%%-H); M=$(date +%%-M); M=$(( M + 2 )); "
            "if [ $M -ge 60 ]; then M=$(( M - 60 )); H=$(( (H + 1) %% 24 )); fi; "
            "LINE=$(grep -m1 -o 'cd .*today.py' \"$HOME/sb04-install.log\"); echo \"line printed by the installer: $LINE\"; %s"
            "printf '%%s %%s * * * { %%s ; } >> %s 2>&1\\n* * * * * echo cron-is-running >> /tmp/cron-alive.log\\n' \"$M\" \"$H\" \"$LINE\" | crontab - && crontab -l; "
            "sleep 170; echo '--- control job (proves cron itself runs):'; cat /tmp/cron-alive.log; "
            "echo '--- what the line printed when cron ran it:'; cat %s; crontab -r; "
            "test -s %s && ! grep -q -i -E 'Traceback|not found|No such file|too many|Operation not permitted' %s"
            % (log, fix, log, log, log, log))


def cron_steps():
    return [check("crontab-line-as-printed", cron_test(False),
                  "the crontab line the installer prints for a Mac, run by the real cron 2 minutes later", cwd="~", timeout=260),
            dict(check("crontab-line-mac-repair", cron_test(True),
                       "the same line with the folder name quoted and python3: does cron then make the morning list?",
                       cwd="~", timeout=260), counts=False)]

SPECS["outliers-sb-04-operations"] = {"steps": [
    prereq("outliers-sb-01-memory"), prereq("outliers-sb-02-standards"), prereq("outliers-sb-03-capture"),
    clone("outliers-sb-04-operations"),
    run("install", "python install.py | tee ~/sb04-install.log", "README, 'What this does about it' (tee added to keep the printed crontab line)",
        stdin=ENTER, expect=r"Installed the record", check="test -f \"$HOME/Documents/Second Brain/_engine/today.py\""),
    {"id": "start-at-login", "kind": "launchd", "expect_plist": True,
     "what": "does the installer put the morning list on a Mac clock (a LaunchAgent)?"},
    run("today", "python _engine/today.py", "README, 'Then:'", cwd=VAULT),
    run("ledger", "python _engine/ledger.py", "README, 'Then:'", cwd=VAULT),
] + cron_steps() + [
]}

SPECS["outliers-second-brain"] = {"steps": [
    clone("outliers-second-brain", source="README, top"),
    run("install", "python install.py | tee ~/sb04-install.log", "README, top (tee added to keep the printed crontab line)",
        stdin=ENTER, timeout=900,
        check="test -f \"$HOME/Documents/Second Brain/_engine/today.py\" && test -f \"$HOME/Documents/Second Brain/_engine/doctor.py\""),
    {"id": "start-at-login", "kind": "launchd", "expect_plist": True,
     "what": "does the installer put the morning list on a Mac clock (a LaunchAgent)?"},
    run("doctor", "python _engine/doctor.py", "Part 2 guide", cwd=VAULT, ok=[0, 1]),
    run("today", "python _engine/today.py", "Part 4 guide", cwd=VAULT),
    run("ledger", "python _engine/ledger.py", "Part 4 guide", cwd=VAULT),
] + cron_steps() + [
] + tests(["python parts/02-standards/tests/test_check_does_not_cry_wolf.py",
           "python parts/02-standards/tests/test_repair_only_when_certain.py",
           "python parts/03-capture/tests/test_youtube_words.py"], "parts/*/tests (no command printed)")}

# ============================================================== CRM set (Session 1)
SPECS["outliers-crm-01-foundation"] = {"steps": crm_install("outliers-crm-01-foundation") + [
    nul_check(),
    check("crm-built", "ls -la ~/CRM ~/CRM/People ~/CRM/_layers; cat ~/.outliers-crm; git -C ~/CRM log --oneline -3",
          "the folders, the pointer file and the first commit are there", cwd="~"),
]}

SPECS["outliers-crm-02-rules"] = {"steps": crm_prereqs(1) + crm_install("outliers-crm-02-rules") + [
    run("stats", "python _engine/identity.py stats", "README, 'Try it'", cwd=CRM),
    run("who", "python _engine/identity.py who \"a name\"", "README, 'Try it'", cwd=CRM, ok=[0, 1]),
    run("duplicates", "python _engine/identity.py duplicates", "README, 'Try it'", cwd=CRM),
    run("collisions", "python _engine/identity.py collisions", "README, 'Try it'", cwd=CRM),
    run("contract", "python _engine/schema.py contract", "README, 'Try it'", cwd=CRM),
    run("sweep", "python _engine/schema.py sweep", "README, 'Try it'", cwd=CRM, ok=[0, 1]),
] + tests(["python tests/test_identity_resolution.py", "python tests/test_schema_contract.py"], "README, 'Run the tests'")}

SPECS["outliers-crm-03-records"] = {"steps": crm_prereqs(2) + crm_install("outliers-crm-03-records") + [
    run("types", "python _engine/ledger.py types", "README", cwd=CRM),
    run("stats", "python _engine/ledger.py stats", "README", cwd=CRM),
    run("tail", "python _engine/ledger.py tail 20", "README", cwd=CRM),
    run("show", "python _engine/derive.py show \"a name or link\"", "README", cwd=CRM, ok=[0, 1]),
    run("quiet", "python _engine/derive.py quiet 60", "README", cwd=CRM),
    run("summary", "python _engine/derive.py summary", "README", cwd=CRM),
] + tests(["python tests/test_ledger_and_derive.py"], "README, tests")}

SPECS["outliers-crm-04-capture"] = {"steps": crm_prereqs(3) + crm_install("outliers-crm-04-capture") + [
    check("make-a-made-up-export", "mkdir -p ~/exports && printf 'First Name,Last Name,URL,Email Address,Company,Position,Connected On\\n"
          "Sam,Testperson,https://www.linkedin.com/in/sam-testperson-000,,Made Up Ltd,Owner,01 Sep 2026\\n' > ~/exports/connections.csv && cat ~/exports/connections.csv",
          "a 1-row made-up LinkedIn export for the collector to read", cwd="~"),
    run("list", "python _engine/collect.py list", "README", cwd=CRM),
    run("dry-run", "python _engine/collect.py run connections ~/exports/connections.csv --dry-run", "README", cwd=CRM, ok=[0, 1]),
    run("run", "python _engine/collect.py run connections ~/exports/connections.csv", "README", cwd=CRM, ok=[0, 1]),
    run("all", "python _engine/collect.py all", "README", cwd=CRM, ok=[0, 1]),
    run("due", "python _engine/refresh.py due", "README", cwd=CRM),
    run("tiers", "python _engine/refresh.py tiers", "README", cwd=CRM),
    run("person", "python _engine/ledger.py person \"Sam Testperson\"", "README", cwd=CRM, ok=[0, 1]),
    run("quiet", "python _engine/derive.py quiet 60", "README", cwd=CRM),
] + tests(["python tests/test_capture.py", "python tests/test_refresh_tiers.py", "python tests/test_atomic_writes.py"], "README, tests")}

SPECS["outliers-crm-05-judgement"] = {"steps": crm_prereqs(4) + crm_install("outliers-crm-05-judgement") + [
    run("agent-check", "python _engine/agent_check.py _agents/", "README", cwd=CRM, ok=[0, 1]),
    run("claude-agents", "", "README: the agent templates", not_testable=CLAUDE_NOT_TESTABLE),
] + tests(["python tests/test_agent_definitions.py", "python tests/test_provenance_and_staging.py"], "README, tests")}

SPECS["outliers-crm-06-safety"] = {"steps": crm_prereqs(5) + crm_install("outliers-crm-06-safety") + [
    run("hold", "python _engine/holds.py hold \"Someone You Know\" \"testing the gate\"", "README, 'Prove it to yourself'", cwd=CRM),
    run("sendgate-refuses", "python _engine/sendgate.py \"Someone You Know\"", "README, 'Prove it to yourself'", cwd=CRM,
        ok="any", expect=r"(?i)hold|refus|block|no\b"),
    run("release", "python _engine/holds.py release \"Someone You Know\"", "README, 'Prove it to yourself'", cwd=CRM),
] + tests(["python tests/test_holds.py", "python tests/test_shared_limits_and_browser.py", "python tests/test_sequence_and_review.py",
           "python tests/test_send_gate_refuses.py", "python tests/test_nothing_can_send.py"], "README, 'Run the tests'")}

SPECS["outliers-crm-07-today"] = {"steps": crm_prereqs(6) + crm_install("outliers-crm-07-today") + [
    run("today-write", "python _engine/today.py --write", "README, 'Build the page'", cwd=CRM, check="test -f ~/CRM/Today.md && head -30 ~/CRM/Today.md"),
] + tests(["python tests/test_today.py"], "README, tests")}

SPECS["outliers-crm-08-verification"] = {"steps": crm_prereqs(7) + crm_install("outliers-crm-08-verification") + [
    run("fourbox", "python _engine/fourbox.py reply_in meeting_booked --within 30", "README", cwd=CRM, ok=[0, 1]),
    run("watchdog", "python _engine/watchdog.py", "README, 'Is it working'", cwd=CRM, ok=[0, 1, 2]),
] + tests(["python tests/test_fourbox.py", "python tests/test_watchdog.py"], "README, tests")}

# ============================================================== Gather set (Session 2)
PW_NOTE = "Playwright's own Chromium, which the installer asks for"
SPECS["outliers-gather-01-foundation"] = {"steps": crm_prereqs(6) + [
    run("python-version", "python --version", "README, 'Before you start'", cwd="~"),
    clone("outliers-gather-01-foundation"),
    run("install", "python install.py", "README, Install", stdin=ENTER,
        check="test -f ~/CRM/_engine/gather.py"),
    run("pip-playwright", "pip install playwright", "README, 'If Playwright is missing'", timeout=600),
    run("playwright-chromium", "playwright install chromium", "README, 'If Playwright is missing'", timeout=900),
    run("status", "python gather.py status", "README, 'Use it'", cwd="~/CRM/_engine", expect=r"(?i)blocked"),
    run("login", "python gather.py login", "README, 'Use it'", cwd="~/CRM/_engine", kind="interactive", wait=35,
        what="opens the sign-in browser; the harness photographs the screen, then presses Enter (no LinkedIn sign-in is made)"),
    run("status-again", "python gather.py status", "README, 'Run status again'", cwd="~/CRM/_engine", expect=r"(?i)blocked"),
    run("linkedin-sign-in", "", "README, 'sign in once'", not_testable="needs a person to sign in to LinkedIn by hand"),
] + tests(["python tests/test_doorman.py"], "README, 'The tests are the proof'")}

SPECS["outliers-gather-02-basics"] = {"steps": crm_prereqs(6) + [
    prereq("outliers-gather-01-foundation"),
    clone("outliers-gather-02-basics"),
    run("install", "python install.py", "README, Install", stdin=ENTER, check="test -f ~/CRM/_engine/gather.py"),
    run("status", "python gather.py status", "README, 'The order to run them in'", cwd="~/CRM/_engine", expect=r"(?i)blocked"),
    check("make-a-made-up-export", "mkdir -p ~/exports && printf 'First Name,Last Name,URL,Email Address,Company,Position,Connected On\\n"
          "Sam,Testperson,https://www.linkedin.com/in/sam-testperson-000,,Made Up Ltd,Owner,01 Sep 2026\\n' > ~/exports/connections.csv",
          "a 1-row made-up LinkedIn export", cwd="~"),
    run("find-export", "python gather.py find export ~/exports/connections.csv", "README, 'The order to run them in'", cwd="~/CRM/_engine", ok=[0, 1, 2]),
    run("find-export-commit", "python gather.py find export ~/exports/connections.csv --commit", "README", cwd="~/CRM/_engine", ok=[0, 1, 2]),
    run("live-jobs", "", "README: undo / find connections / ask / accepted", not_testable="need a signed-in LinkedIn browser"),
] + tests(["python tests/test_jobs.py"], "README, 'The tests are the proof'")}

SPECS["outliers-gather-04-facebook"] = {"steps": crm_prereqs(6) + [
    run("python-version", "python3 --version", "README, 'Before you start'", cwd="~"),
    clone("outliers-gather-04-facebook"),
    run("install", "python3 install.py", "README, Install (written for a Mac)", stdin=ENTER, check="test -f ~/CRM/_engine/facebook.py"),
    run("playwright-venv", "python3 -m venv .venv && source .venv/bin/activate && pip install playwright && playwright install chromium",
        "README, 'Playwright, once' (4 lines, run in one Terminal window)", timeout=900),
    run("status", "source ~/outliers-gather-04-facebook/.venv/bin/activate && python3 facebook.py status",
        "README, 'Use it' (after 'source .venv/bin/activate', as the README says for each new window)", cwd="~/CRM/_engine", expect=r"(?i)blocked"),
    run("login", "source ~/outliers-gather-04-facebook/.venv/bin/activate && python3 facebook.py login", "README, 'Use it'",
        cwd="~/CRM/_engine", kind="interactive", wait=35,
        what="opens the sign-in browser; photographed, then Enter pressed (no Facebook sign-in is made)"),
    run("facebook-sign-in", "", "README", not_testable="needs a person to sign in to Facebook by hand; find-groups/join need that session"),
] + tests(["python3 tests/test_governor.py"], "README, 'The tests are the proof'")}

SPECS["outliers-gather-05-timetable"] = {"steps": crm_prereqs(1) + [
    clone("outliers-gather-05-timetable"),
    run("install", "python install.py", "README, Install (Enter for each default: empty timetable, start at login = yes)",
        stdin=ENTER, check="test -f ~/CRM/_engine/timetable.py"),
    {"id": "start-at-login", "kind": "launchd", "cwd": "~/CRM/_engine", "wait": 15,
     "what": "the LaunchAgent the installer writes; is the loop alive after bootstrap?",
     "check": "python3 timetable.py status", "check_tries": 3, "log_glob": "../_state/timetable/*.log"},
    run("list", "python timetable.py list", "README, 'Use it'", cwd="~/CRM/_engine"),
    run("add", "python timetable.py add \"echo hello from the timetable\" --at 09:30 --days mon,tue,wed,thu,fri --label \"mac test\"",
        "README, 'Use it'", cwd="~/CRM/_engine"),
    run("dry-run", "python timetable.py run --dry-run", "README, 'Look before you leap'", cwd="~/CRM/_engine"),
    run("status", "python timetable.py status", "README", cwd="~/CRM/_engine", ok=[0, 1]),
    run("stop", "python timetable.py stop", "README", cwd="~/CRM/_engine", ok=[0, 1]),
    run("start", "python timetable.py start", "README", cwd="~/CRM/_engine", timeout=60),
    run("status-after-start", "python timetable.py status", "README", cwd="~/CRM/_engine", ok=[0, 1]),
    run("stop-again", "python timetable.py stop", "README", cwd="~/CRM/_engine", ok=[0, 1]),
    run("remove-startup", "python timetable.py install-startup --remove", "timetable.py's own message 'To undo it'",
        cwd="~/CRM/_engine", ok=[0, 1], what="the only uninstall there is: take the login job away"),
] + tests(["python tests/test_timetable.py"], "README, 'The tests are the proof'")}

# ============================================================== single-purpose repos
SPECS["outliers-seven-ratings"] = {"steps": [
    run("git-version", "git --version", "README Step 2, Mac", cwd="~"),
    run("install-claude-code", "curl -fsSL https://claude.ai/install.sh | bash", "README Step 3, Mac", cwd="~", timeout=600),
    run("claude-version", "claude --version", "README Step 3", cwd="~",
        subs=["export PATH=\"$HOME/.local/bin:$PATH\"; claude --version"],
        what="in the same window, as the README says a new window may be needed"),
    run("claude-version-new-window", "zsh -l -i -c 'claude --version'", "README Step 3 ('open a new one')", cwd="~",
        subs=["export PATH=\"$HOME/.local/bin:$PATH\"; claude --version"]),
    run("log-in", "", "README Step 4", not_testable=CLAUDE_NOT_TESTABLE),
    run("clone", "cd ~ && git clone https://github.com/OUTLIERS-ai/outliers-seven-ratings.git && cd outliers-seven-ratings && ls",
        "README Step 5, Mac", cwd="~", expect=r"SEND-AI-Working-Assessment\.md", no_auto_retry=True),
    run("assessment", "", "README Steps 6-7 (claude --add-dir ~)", not_testable=CLAUDE_NOT_TESTABLE),
]}

SPECS["outliers-critic"] = {"notes": ["README gives no command: 'Drop the-critic.md into your agents folder'"], "steps": [
    clone("outliers-critic"),
    check("install-by-copying", "mkdir -p ~/.claude/agents && cp the-critic.md design-critique-canon.md ~/.claude/agents/ && ls -la ~/.claude/agents",
          "README 'Installing it': copy the 2 files into ~/.claude/agents (no command printed)"),
    check("paths-in-the-agent-file", "grep -n -F 'Projects\\' the-critic.md | head -20; ! grep -q -F 'Projects\\' the-critic.md",
          "does the agent file use Windows backslash paths, which a Mac reads as part of a file name?"),
    run("run-the-critic", "", "README", not_testable=CLAUDE_NOT_TESTABLE),
]}

SPECS["outliers-diagrams"] = {"steps": [
    clone("outliers-diagrams"),
    run("pip-playwright", "pip install playwright", "README, 'Running it'", timeout=600),
    run("chromium", "python -m playwright install chromium", "README, 'Running it'", timeout=900),
    run("make-diagrams", "python make_diagrams.py", "README, 'Running it'", timeout=600,
        check="ls png/*.png | wc -l; test $(ls png/*.png | wc -l) -ge 10 && mkdir -p $OUT/shots && cp png/*.png $OUT/shots/ 2>/dev/null; true"),
    check("fonts", "fc-list 2>/dev/null | grep -i -E 'constantia|consolas' || system_profiler SPFontsDataType 2>/dev/null | grep -i -E 'constantia|consolas' || echo 'Constantia and Consolas are NOT on this Mac'; "
          "system_profiler SPFontsDataType 2>/dev/null | grep -q -i constantia",
          "are the 2 Microsoft fonts the drawings are set in present on a Mac?", timeout=300),
    run("lab-colour", "python labs/colour_measure.py", "labs/README.md", timeout=300, ok=[0, 1]),
    run("lab-phone", "python labs/phone_width.py", "labs/README.md", timeout=300, ok=[0, 1]),
    run("lab-ten", "python labs/ten_design_systems.py", "labs/README.md", timeout=400, ok=[0, 1]),
    run("lab-background", "python labs/what_a_background_is_for.py", "labs/README.md", timeout=300, ok=[0, 1]),
]}

SPECS["fathom-meeting-agent"] = {"steps": [
    run("clone", "git clone https://github.com/OUTLIERS-ai/fathom-meeting-agent.git", "README 1, Step 1", cwd="~",
        check="test -d ~/fathom-meeting-agent", no_auto_retry=True),
    run("pip-playwright", "pip install playwright", "README 1, Step 2", timeout=600),
    run("chromium", "playwright install chromium", "README 1, Step 2", timeout=900),
    run("open-playwright-browser", "", "README 1, Step 3 'Open the browser Playwright just installed'",
        not_testable="the README gives no command for opening that browser, and the Fathom sign-in is by hand"),
    run("check-fathom", "", "README 1, Step 4 ('check Fathom' in Claude Code)", not_testable=CLAUDE_NOT_TESTABLE),
]}

# ============================================================== Workspace set (Session 7)
WS_VAULTS = [prereq("outliers-sb-01-memory"), prereq("outliers-crm-01-foundation")]

SPECS["outliers-ws-01-agent-flow"] = {"steps": WS_VAULTS + [
    claude_code_prereq(),
    run("versions", "python --version; node --version", "README, 'What you need'", cwd="~",
        subs=["python3 --version; node --version"]),
    clone("outliers-ws-01-agent-flow", source="README, top (run from the home folder)"),
    run("install", "python install.py", "README, top ('On a Mac, type python3')", stdin=ENTER, timeout=900,
        check="ls ~/Library/LaunchAgents/ && python3 -c \"import json,os;d=json.load(open(os.path.expanduser('~/.claude/settings.json')));print(list(d.get('hooks',{})))\""),
    {"id": "start-at-login", "kind": "launchd", "wait": 20, "cwd": "{repo}",
     "what": "the login job the installer wrote: bootstrap it and see if the page on 3001 answers",
     "check": "curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:3001 | grep -E '^(2|3)'", "check_tries": 24,
     "log_glob": "logs/*.log"},
    {"id": "page-3001", "kind": "shot", "url": "http://127.0.0.1:3001", "desktop": True, "wait": 20,
     "what": "the live agent-flow page"},
    run("status", "python start.py --status", "README, 'Useful commands'", ok=[0, 1]),
    run("check-hooks", "python check_hooks.py", "README, 'Useful commands'", ok=[0, 1]),
    run("cleanup-dry-run", "python cleanup.py --dry-run", "README, 'Useful commands'"),
    run("start-now", "python install.py --start-now", "README, 'Useful commands'", stdin=ENTER, timeout=600,
        check="curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:3001 | grep -E '^(2|3)'"),
    run("stop", "python start.py --stop", "README, fault 4", ok=[0, 1]),
    run("pip-pytest", "python -m pip install pytest", "README, tests", timeout=600),
    run("tests", "python -m pytest -q", "README, tests/ row", timeout=900),
    run("new-claude-session", "", "README: 'start a NEW Claude Code session inside the watch folder'", not_testable=CLAUDE_NOT_TESTABLE),
    run("uninstall", "python install.py --uninstall", "README, 'Useful commands'", stdin=ENTER,
        check="! ls ~/Library/LaunchAgents/*agent* 2>/dev/null"),
]}

SPECS["outliers-ws-02-fleetview"] = {"steps": WS_VAULTS + [
    claude_code_prereq(),
    run("versions", "node --version; python --version", "README, 'What it needs'", cwd="~",
        subs=["node --version; python3 --version"]),
    clone("outliers-ws-02-fleetview", source="README, top"),
    run("install", "python install.py", "README, top ('Say yes when it offers to start FleetView')", stdin=ENTER, timeout=900,
        check="curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://localhost:3010/graph.html | grep -E '^2'"),
    {"id": "page-3010", "kind": "shot", "url": "http://localhost:3010/graph.html", "desktop": True, "wait": 30,
     "what": "FleetView started by the installer"},
    dict(check("token-panel-as-installer-started-it", "sleep 20; curl -s http://127.0.0.1:3010/api/usage; echo; ! curl -s http://127.0.0.1:3010/api/usage | grep -i 'could not run'",
               "the token panel of the FleetView the installer started (no Claude Code sessions exist on this machine)", timeout=120), counts=False),
    check("ccusage-with-terminal-path", "npx -y ccusage@20.0.24 claude daily --json; echo \"exit $?\"; command -v npx",
          "the token panel's command, with the PATH a Terminal window has", timeout=300),
    check("ccusage-with-login-job-path", "env -i HOME=$HOME PATH=/usr/bin:/bin:/usr/sbin:/sbin /bin/sh -c 'npx -y ccusage@20.0.24 claude daily --json'",
          "the same command with the PATH launchd gives a login job (/usr/bin:/bin:/usr/sbin:/sbin), which the FleetView LaunchAgent does not change",
          timeout=300),
    run("stop", "python install.py --stop", "README, top", ok=[0, 1]),
    {"id": "start-at-login", "kind": "launchd", "wait": 15,
     "what": "the login job: bootstrap it; the page should answer and the token panel should run",
     "check": "curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://localhost:3010/graph.html | grep -E '^2' && sleep 25 && "
              "echo 'token panel under launchd:' && curl -s http://127.0.0.1:3010/api/usage",
     "check_tries": 6, "log_glob": "fleetview.log"},
    run("start", "python install.py --start", "README, top", ok=[0, 1]),
    run("stop-2", "python install.py --stop", "README, top", ok=[0, 1]),
    run("npm-install", "npm install", "README, 'see it before your own sessions exist'", timeout=600),
    {"id": "demo", "kind": "serve", "cmd": "npm run demo", "url": "http://localhost:3011/graph.html", "wait": 60,
     "source": "README, 'npm run demo'", "desktop": False, "what": "made-up sessions on 3011"},
    run("npm-test", "npm test", "README, Commands", timeout=900),
    run("pip-pytest", "python -m pip install pytest", "README, Commands", timeout=600),
    run("pytest", "python -m pytest -q", "README, Commands", timeout=900),
    run("uninstall", "python install.py --uninstall", "README, Commands", stdin=ENTER,
        check="! ls ~/Library/LaunchAgents/ | grep -i fleet"),
]}

SPECS["outliers-ws-03-projectforge"] = {"steps": WS_VAULTS + [
    claude_code_prereq(),
    clone("outliers-ws-03-projectforge", source="README, top"),
    run("install", "python install.py", "README, top (Enter for every default, including 'Go ahead?')", stdin=ENTER, timeout=600,
        check="test -f data/forge.db && test -f ~/.claude/projectforge/forge_agent.py"),
    {"id": "board", "kind": "serve", "cmd": "python forge.py serve", "url": "http://127.0.0.1:3020", "wait": 40,
     "source": "README, 'Everyday commands'", "desktop": True, "what": "the web board"},
    run("list", "python forge.py list", "README, 'Everyday commands'"),
    run("projects", "python forge.py projects", "README, 'Everyday commands'"),
    run("add-project", "python forge.py add-project \"Content week 39\" --dept content --actor you", "README, 'Everyday commands'", ok=[0, 1, 2]),
    run("waiting", "python forge.py waiting", "README, 'Everyday commands'"),
    run("agent-tool-guide-mac-lines",
        "forge=~/.claude/projectforge/forge_agent.py\npython $forge open --agent content-lead --dept content --project \"Content week 39\" --title \"Newsletter\" --assignee writer-bot",
        "guide/GUIDE.md 'What your agents run': the Mac first line, then 'the same second line'", cwd="~",
        ok=[0, 1, 2], expect=r"(?i)refused|opened|card", what="the guide says a worker is refused unless a manager was named at install"),
    {"id": "demo-board", "kind": "serve", "cmd": "python tools/demo_board.py --out demo --serve", "url": "http://127.0.0.1:3029",
     "wait": 40, "source": "README, 'Everyday commands'", "what": "the demo board of made-up work"},
    run("schedule-print", "python tools/schedule.py --print", "README, 'Everyday commands'"),
    run("schedule-install", "python tools/schedule.py --install", "tools/schedule.py --help (the optional Mac schedule)", ok=[0, 1]),
    {"id": "start-at-login", "kind": "launchd", "wait": 20,
     "what": "the optional clock job; it starts claude, which is not logged in here",
     "check": "launchctl print gui/$(id -u) | grep -i forge"},
    run("schedule-remove", "python tools/schedule.py --remove", "tools/schedule.py", ok=[0, 1]),
    run("start-with-computer", "python install.py --start-with-computer --yes", "README, 'What the installer does' (question 9 = yes)",
        stdin=ENTER, timeout=300),
    {"id": "board-at-login", "kind": "launchd", "wait": 15, "match": "(?i)forge|projectforge",
     "what": "the file that starts the board when the Mac logs in: bootstrap it, the board should answer on 3020",
     "check": "curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:3020 | grep -E '^(2|3)'", "check_tries": 12},
    {"id": "board-page-from-login-job", "kind": "shot", "url": "http://127.0.0.1:3020", "wait": 20, "what": "the board started by launchd"},
    run("serve-stop", "python forge.py serve --stop", "README, 'Everyday commands'", ok=[0, 1]),
    run("forge-run", "", "README: /forge-run in Claude Code", not_testable=CLAUDE_NOT_TESTABLE),
    run("pip-pytest", "python -m pip install pytest", "README, Needs", timeout=600),
    run("tests", "python -m pytest -q", "README, Needs", timeout=900),
    run("uninstall", "python install.py --uninstall", "README, 'What the installer does'", stdin="y\n" + ENTER, ok=[0],
        check="test ! -f ~/.claude/projectforge/forge_agent.py"),
]}

SPECS["outliers-ws-04-jeeves"] = {"steps": WS_VAULTS + [
    claude_code_prereq(),
    clone("outliers-ws-04-jeeves", source="README, top"),
    run("install", "python install.py", "README, top and Install (Enter for each default)", stdin=ENTER, timeout=600,
        check="test -f config.json && cat config.json"),
    {"id": "jeeves-page", "kind": "serve", "cmd": "python start.py", "url": "http://127.0.0.1:4040/", "wait": 40,
     "source": "README, 'Start and stop'", "desktop": True, "what": "Jeeves over the test vaults",
     "check": "curl -s http://127.0.0.1:4040/api/health"},
    run("demo-data", "python tools/demo.py ../jeeves-demo", "README, 'Try it on made-up data first' (build only)", ok=[0, 1], timeout=300),
    {"id": "demo-page", "kind": "serve", "cmd": "python tools/demo.py ../jeeves-demo --serve --port 4099", "url": "http://127.0.0.1:4099/",
     "wait": 60, "source": "README, 'Try it on made-up data first'", "what": "Sam the bookkeeper"},
    run("launcher", "python install.py --launcher --yes", "README ('asks whether to start Jeeves hidden when you log in')", stdin=ENTER, timeout=300),
    {"id": "start-at-login", "kind": "launchd", "wait": 15,
     "what": "the login job: bootstrap it; Jeeves should answer on 4040",
     "check": "curl -s --max-time 5 http://127.0.0.1:4040/api/health", "check_tries": 12},
    run("stop", "python start.py --stop", "README, 'Start and stop'", ok=[0, 1]),
    run("chat", "", "README: the Chat panel", not_testable=CLAUDE_NOT_TESTABLE),
    run("pip-pytest", "python -m pip install pytest", "README, Tests", timeout=600),
    run("tests", "python -m pytest -q", "README, Tests", timeout=900),
    run("uninstall", "python install.py --uninstall", "README, Uninstall", stdin=ENTER,
        check="! ls ~/Library/LaunchAgents/ | grep -i jeeves"),
]}

SKIPPED = {"outliers-content-engine": "private repo: a public repo's workflow cannot clone it without a stored secret, and this repo holds none"}


def get(repo):
    return SPECS[repo]


if __name__ == "__main__":
    import json
    import sys
    only = [s.strip() for s in (sys.argv[1] if len(sys.argv) > 1 else "").split(",") if s.strip()]
    macs = [s.strip() for s in (sys.argv[2] if len(sys.argv) > 2 else "macos-15,macos-15-intel").split(",") if s.strip()]
    repos = [r for r in SPECS if not only or r in only]
    # Session 7 repos last, so the push being made today has the longest time to land.
    repos.sort(key=lambda r: r.startswith("outliers-ws-"))
    include = [{"repo": r, "os": m} for r in repos for m in macs]
    print(json.dumps({"include": include}))
