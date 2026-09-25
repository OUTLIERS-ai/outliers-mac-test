"""Picture scenario for the Jeeves Mac guide (wave 6, 2026-09-25).

Runs in a made-up home folder, /Users/sam (like the Windows guide's made-up C:\\Users\\sam), so no
picture shows the test Mac's own user name. Every step is the command a Mac member types, with its
printed output kept whole for Mac-Versions/mac-shots/draw_terminal.py:

  checks          python3 --version, claude --version, git --version  (the "Before you start" picture)
  install         python3 install.py, Enter at every question         (the install picture)
  install-again   the same again                                      ("Nothing changed")
  new-member      the page of a brand-new setup                        (empty panels say what is missing)
  already-running python3 start.py while Jeeves already runs          ("already running")
  folder-missing  the page with second_brain pointing at a folder that is not there

Never used for a "What was run on a Mac" box.
"""
import specs_mac as SM

W = SM.W
SAM = "/Users/sam"
ENV = {"HOME": SAM}
REPO = SAM + "/outliers-ws-04-jeeves-mac"
ENTER = SM.ENTER


def sam(step):
    step = dict(step)
    step["env"] = dict(ENV, **step.get("env", {}))
    step.setdefault("counts", False)
    return step


def chk(id_, cmd, what, cwd=REPO, **kw):
    kw.setdefault("ok", "any")
    return sam(SM.check(id_, cmd, what, cwd=cwd, **kw))


MISSING = ("python3 -c \"import json;c=json.load(open('config.json'));"
           "c['second_brain']='/Users/sam/Second Brain (old laptop)';"
           "json.dump(c,open('config.json','w'),indent=2)\"")

SPEC = {"steps": [
    W.claude_code_prereq(),
    SM.check("setup-sam", "sudo mkdir -p /Users/sam && sudo chown $(id -un) /Users/sam && "
             "mkdir -p /Users/sam/.local/bin && cp -L ~/.local/bin/claude /Users/sam/.local/bin/claude && "
             ": > /Users/sam/.zprofile && "
             "echo 'export PATH=\"$HOME/.local/bin:$PATH\"' > /Users/sam/.zshrc && ls -la /Users/sam /Users/sam/.local/bin",
             "harness: a made-up member home folder, /Users/sam, with Claude Code in ~/.local/bin and the "
             "guide's PATH line in ~/.zshrc", cwd="~", timeout=300),
    chk("python-version", "python3 --version", "Before you start", cwd=SAM),
    chk("claude-version", "claude --version", "Before you start", cwd=SAM),
    chk("git-version", "git --version", "Before you start", cwd=SAM),
    chk("prereq-sb01", "rm -rf ~/outliers-sb-01-memory && git clone -q https://github.com/OUTLIERS-ai/outliers-sb-01-memory "
        "&& cd ~/outliers-sb-01-memory && python3 install.py", "earlier part: the second brain", cwd=SAM,
        stdin=ENTER, timeout=900),
    chk("prereq-crm01", "rm -rf ~/outliers-crm-01-foundation && git clone -q https://github.com/OUTLIERS-ai/outliers-crm-01-foundation "
        "&& cd ~/outliers-crm-01-foundation && python3 install.py", "earlier part: the CRM", cwd=SAM,
        stdin=ENTER, timeout=900),
    chk("clone", "git clone https://github.com/OUTLIERS-ai/outliers-ws-04-jeeves outliers-ws-04-jeeves-mac",
        "the main repo into the -mac folder name (exploratory)", cwd=SAM, timeout=300),
    chk("install", "python3 install.py", "Install step 3, Enter at every question", stdin=ENTER, timeout=600),
    chk("install-again", "python3 install.py", "the same answers again", stdin=ENTER, timeout=600),
    sam({"id": "new-member", "kind": "serve", "cmd": "python3 start.py --no-open", "cwd": REPO,
         "url": "http://127.0.0.1:4040/", "wait": 40, "settle": 8, "source": "When it goes wrong",
         "what": "a brand-new setup: every empty panel says what is missing"}),
    chk("already-running", "python3 start.py --no-open > /tmp/jeeves-bg.log 2>&1 &\nsleep 12\n"
        "echo '=== typed: python3 start.py'\npython3 start.py\necho '=== typed: python3 start.py --stop'\n"
        "python3 start.py --stop\nsleep 2", "starting Jeeves when it already runs", timeout=120),
    sam({"id": "folder-missing", "kind": "serve", "cmd": MISSING + " && python3 start.py --no-open", "cwd": REPO,
         "url": "http://127.0.0.1:4040/", "wait": 40, "settle": 8, "source": "When it goes wrong",
         "what": "second_brain names a folder that is not there"}),
    chk("stop-last", "python3 start.py --stop; cat config.json", "harness: stop, and show the settings used", timeout=120),
]}
