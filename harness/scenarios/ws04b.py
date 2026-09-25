"""Behaviour checks for the Jeeves Mac guide, round 2 (wave 6, 2026-09-25). Tested before the guide is reworded.

Runs in a made-up home folder, /Users/sam, as ws04.py does. Never used for a "What was run on a Mac" box.

  1. crm-layer1       what a new member's CRM (the first CRM session's download only) contains: is
                      _engine/today.py there?
  2. install-with-crm python3 install.py, Return at every question, with a CRM at ~/CRM: what the CRM
                      question suggests and what Return keeps (config.json after)
  3. today-hint       the page's Today answer for that CRM (/api/today) and a picture of the page
  4. no-crm           ~/CRM moved away and the CRM's pointer file too (a member with no CRM): what the
                      question shows and what Return does
  5. crm-moved        ~/CRM moved away but the pointer file left (a member who moved their CRM): what
                      Return does then
  6. npm-global       npm install -g ccusage with nodejs.org's Node, as the Jeeves guide prints it; then
                      ccusage --version; if refused, the forms that might work without sudo
  7. install-now      the installer's full output now (for the pictures), and --uninstall on a Mac
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
    kw.setdefault("timeout", 600)
    return sam(SM.check(id_, cmd, what, cwd=cwd, **kw))


SPEC = {"steps": [
    W.claude_code_prereq(),
    SM.check("setup-sam", "sudo mkdir -p /Users/sam && sudo chown $(id -un) /Users/sam && "
             "mkdir -p /Users/sam/.local/bin && cp -L ~/.local/bin/claude /Users/sam/.local/bin/claude && "
             ": > /Users/sam/.zprofile && "
             "echo 'export PATH=\"$HOME/.local/bin:$PATH\"' > /Users/sam/.zshrc && ls -la /Users/sam",
             "harness: a made-up member home folder", cwd="~", timeout=300),
    chk("versions", "python3 --version; node --version; npm --version; claude --version; git --version", "versions", cwd=SAM),
    chk("prereq-sb01", "git clone -q https://github.com/OUTLIERS-ai/outliers-sb-01-memory "
        "&& cd ~/outliers-sb-01-memory && python3 install.py", "earlier part: the second brain", cwd=SAM,
        stdin=ENTER, timeout=900),
    chk("prereq-crm01", "git clone -q https://github.com/OUTLIERS-ai/outliers-crm-01-foundation "
        "&& cd ~/outliers-crm-01-foundation && python3 install.py", "earlier part: the first CRM session", cwd=SAM,
        stdin=ENTER, timeout=900),
    chk("crm-layer1", "ls -la ~/CRM; echo '--- _engine:'; ls -la ~/CRM/_engine 2>&1; "
        "test -f ~/CRM/_engine/today.py && echo 'TODAY_PY: present' || echo 'TODAY_PY: absent'; "
        "echo '--- pointer file:'; ls -la ~/.outliers-crm 2>&1; cat ~/.outliers-crm 2>&1", "what the first CRM session leaves", cwd=SAM),
    chk("clone", "git clone https://github.com/OUTLIERS-ai/outliers-ws-04-jeeves outliers-ws-04-jeeves-mac && "
        "git -C outliers-ws-04-jeeves-mac log --oneline -1", "the main repo into the -mac folder name", cwd=SAM, timeout=300),
    chk("install-with-crm", "python3 install.py; echo \"=== exit $?\"; echo '=== config.json:'; cat config.json",
        "Return at every question, CRM at ~/CRM", stdin=ENTER),
    sam({"id": "today-page", "kind": "serve", "cmd": "python3 start.py --no-open", "cwd": REPO,
         "url": "http://127.0.0.1:4040/", "wait": 40, "settle": 8, "source": "behaviour",
         "what": "the page for a new member whose CRM has the first session only",
         "check": "curl -s http://127.0.0.1:4040/api/today; echo; curl -s http://127.0.0.1:4040/api/apps"}),
    chk("stop-1", "python3 start.py --stop", "harness: stop"),
    chk("no-crm", "mkdir -p /tmp/crm-away && mv ~/CRM /tmp/crm-away/ && (mv ~/.outliers-crm /tmp/crm-away/ 2>/dev/null; true) && "
        "mv config.json /tmp/crm-away/config-1.json && python3 install.py; echo \"=== exit $?\"; "
        "echo '=== config.json:'; cat config.json 2>&1", "no CRM and no pointer file: Return at every question", stdin=ENTER),
    chk("crm-moved", "(test -f /tmp/crm-away/.outliers-crm && cp /tmp/crm-away/.outliers-crm ~/.outliers-crm; true) && "
        "(mv config.json /tmp/crm-away/config-2.json 2>/dev/null; true) && cat ~/.outliers-crm 2>&1; "
        "python3 install.py; echo \"=== exit $?\"; echo '=== config.json:'; cat config.json 2>&1",
        "CRM moved away, pointer file left: Return at every question", stdin=ENTER),
    chk("crm-back", "mv /tmp/crm-away/CRM ~/CRM; (mv /tmp/crm-away/config-1.json config.json; true); ls ~/CRM | head -5",
        "harness: put the CRM and the first settings back"),
    chk("npm-global", "command -v node npm; npm config get prefix; ls -ld \"$(npm config get prefix)/lib/node_modules\"; "
        "npm install -g ccusage; echo \"=== npm install -g exit $?\"; ccusage --version; echo \"=== ccusage exit $?\"",
        "npm install -g ccusage as the guide prints it, nodejs.org's Node", cwd=SAM),
    chk("npx-form", "npx -y ccusage@20.0.24 --version; echo \"=== npx exit $?\"",
        "the pinned npx form FleetView uses, with no global install", cwd=SAM),
    chk("npm-home-prefix", "mkdir -p ~/.npm-global && npm config set prefix ~/.npm-global && npm install -g ccusage; "
        "echo \"=== exit $?\"; ~/.npm-global/bin/ccusage --version; echo \"=== exit $?\"; npm config delete prefix",
        "a home-folder npm prefix, no sudo", cwd=SAM),
    chk("install-again", "python3 install.py", "the same answers again (picture)", stdin=ENTER),
    chk("launcher", "python3 install.py --launcher --yes; echo \"=== exit $?\"; launchctl list | grep outliers; true",
        "the start-by-itself question answered yes by the switch", timeout=300),
    chk("uninstall", "python3 install.py --uninstall; echo \"=== exit $?\"; sleep 2; echo '=== launchctl list:'; "
        "launchctl list | grep outliers; echo \"=== grep exit $?\"; ls ~/Library/LaunchAgents 2>&1",
        "uninstall on a Mac: does launchctl still list Jeeves?", stdin="y\ny\n" + ENTER, timeout=300),
]}
