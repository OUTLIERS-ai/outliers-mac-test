"""Jeeves pictures after the main-repo pushes (wave 6 round 2, 2026-09-25). Never used for a box.

Made-up home folder /Users/sam, as ws04.py. Clones the main repo (aa80e8a or later: the installer's Mac
start-up words say "switch on your Mac and sign in") into the -mac folder name and keeps whole outputs of:

  install        python3 install.py, Return at every question   (the install picture)
  install-again  the same again                                   (the "Nothing changed" picture)
  work-board     the real Jeeves (not the practice world) with its Work board tab open: the download
                 link a Mac member sees (outliers-ws-03-projectforge-mac)
"""
import specs_mac as SM
from pathlib import Path

SHOT = str(Path(__file__).resolve().parent / "ws04e_shot.py")
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
    kw.setdefault("timeout", 600)
    return sam(SM.check(id_, cmd, what, cwd=cwd, **kw))


SPEC = {"steps": [
    W.claude_code_prereq(),
    SM.check("setup-sam", "sudo mkdir -p /Users/sam && sudo chown $(id -un) /Users/sam && "
             "mkdir -p /Users/sam/.local/bin && cp -L ~/.local/bin/claude /Users/sam/.local/bin/claude && "
             ": > /Users/sam/.zprofile && "
             "echo 'export PATH=\"$HOME/.local/bin:$PATH\"' > /Users/sam/.zshrc && ls -la /Users/sam",
             "harness: a made-up member home folder", cwd="~", timeout=300),
    chk("prereq-sb01", "git clone -q https://github.com/OUTLIERS-ai/outliers-sb-01-memory "
        "&& cd ~/outliers-sb-01-memory && python3 install.py", "earlier part: the second brain", cwd=SAM,
        stdin=ENTER, timeout=900),
    chk("prereq-crm01", "git clone -q https://github.com/OUTLIERS-ai/outliers-crm-01-foundation "
        "&& cd ~/outliers-crm-01-foundation && python3 install.py", "earlier part: the first CRM session", cwd=SAM,
        stdin=ENTER, timeout=900),
    chk("clone", "git clone https://github.com/OUTLIERS-ai/outliers-ws-04-jeeves outliers-ws-04-jeeves-mac && "
        "git -C outliers-ws-04-jeeves-mac log --oneline -1", "the main repo into the -mac folder name", cwd=SAM, timeout=300),
    chk("install", "python3 install.py", "Return at every question", stdin=ENTER),
    chk("install-again", "python3 install.py", "the same answers again", stdin=ENTER),
    chk("shot-tool", "python3 -m venv ~/shootvenv && ~/shootvenv/bin/python -m pip install -q playwright && "
        "~/shootvenv/bin/python -m playwright install chromium > /dev/null && echo ready", "harness only: Playwright",
        cwd=SAM, timeout=900),
    chk("work-board", "python3 start.py --no-open > /tmp/jv.log 2>&1 &\nsleep 12\nmkdir -p \"$OUT/shots\"\n"
        "~/shootvenv/bin/python \"" + SHOT + "\" http://127.0.0.1:4040/ 'WORK BOARD' "
        "\"$OUT/shots/mac-work-board-page.png\"\n"
        "curl -s http://127.0.0.1:4040/api/apps; echo\npython3 start.py --stop",
        "the real Jeeves, Work board tab open", timeout=300),
]}
