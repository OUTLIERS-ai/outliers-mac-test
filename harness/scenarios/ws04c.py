"""Jeeves, ccusage without sudo (wave 6 round 2, 2026-09-25). Never used for a "What was run on a Mac" box.

ws04b showed `npm install -g ccusage` refused with EACCES on nodejs.org's Node (run 36154211225). Jeeves only
uses a `ccusage` it finds on its PATH; when it starts by itself its PATH is ~/.local/bin, ~/.claude/local,
/opt/homebrew/bin and the system folders (install.py mac_path). This tries the form that puts ccusage in
~/.local/bin, the folder the guide's Claude Code line already adds to Terminal's PATH:

  1. npm install -g --prefix ~/.local ccusage     then ccusage --version in a new login shell
  2. Jeeves started with the sign-in PATH only; /api/tokens must say ccusage is available
  3. Jeeves started from Terminal; /api/tokens the same
"""
import specs_mac as SM

W = SM.W
SAM = "/Users/sam"
ENV = {"HOME": SAM}
REPO = SAM + "/outliers-ws-04-jeeves-mac"
ENTER = SM.ENTER
LOGIN_PATH = "/Users/sam/.local/bin:/Users/sam/.claude/local:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"


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
             "harness: a made-up member home folder with the guide's Claude Code PATH line", cwd="~", timeout=300),
    chk("prereq-sb01", "git clone -q https://github.com/OUTLIERS-ai/outliers-sb-01-memory "
        "&& cd ~/outliers-sb-01-memory && python3 install.py", "earlier part: the second brain", cwd=SAM,
        stdin=ENTER, timeout=900),
    chk("clone", "git clone https://github.com/OUTLIERS-ai/outliers-ws-04-jeeves outliers-ws-04-jeeves-mac",
        "the main repo into the -mac folder name", cwd=SAM, timeout=300),
    chk("install", "python3 install.py", "Return at every question", stdin=ENTER),
    chk("npm-local", "npm install -g --prefix ~/.local ccusage; echo \"=== exit $?\"; ls -la ~/.local/bin",
        "the guide's candidate line", cwd=SAM),
    chk("version-new-shell", "command -v ccusage; ccusage --version; echo \"=== exit $?\"",
        "in a new Terminal window (login shell: ~/.zshrc read)", cwd=SAM),
    chk("installer-sees-it", "python3 install.py | grep -i ccusage", "the installer's extras line now", stdin=ENTER),
    chk("tokens-login-path", "env -i HOME=/Users/sam USER=$USER PATH=" + LOGIN_PATH + " python3 start.py --no-open "
        "> /tmp/jv.log 2>&1 &\nsleep 15\ncurl -s http://127.0.0.1:4040/api/tokens; echo\npython3 start.py --stop",
        "Jeeves with only the PATH its LaunchAgent gives it: /api/tokens", timeout=180),
    chk("tokens-terminal", "python3 start.py --no-open > /tmp/jv2.log 2>&1 &\nsleep 15\n"
        "curl -s http://127.0.0.1:4040/api/tokens; echo\npython3 start.py --stop",
        "Jeeves started from Terminal: /api/tokens", timeout=180),
]}
