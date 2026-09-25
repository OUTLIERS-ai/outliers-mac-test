"""Build Your Own Screen (Mac): every line of the guide that a test Mac can run without a Claude Code login.

Wave 6, 2026-09-25 (readers' findings): each printed line gets a status. The guide has no download; the
lines that work on the folder Claude Code writes for you (`claude`, `git log --oneline`, `tail -30
logs/screen.log`, `python3 serve.py`, the screen's own tests) cannot run here and are "read, not run" in
the guide's box. Everything else runs below, exactly as printed, in the guide's order, in a fresh login
shell per line; a `cd` line is followed by lines run in that folder.
Run with: gh workflow run mac-scenario.yml -f repo=my-screen -f scenario=ownscreen
"""
import specs as W
import specs_mac as SM

G = "guide, "
SPEC = {"steps": [
    W.claude_code_prereq(),
    SM.run("python-prefix", 'python3 -c "import sys; print(sys.prefix)"', G + "Before you start on a Mac", cwd="~",
           expect=r"Python[.]framework"),
    SM.run("claude-path", "echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> ~/.zshrc", G + "Before you start on a Mac", cwd="~"),
    SM.run("claude-version", "claude --version", G + "Before you start, table", cwd="~", expect=r"[0-9]+[.][0-9]+"),
    SM.run("python-version", "python3 --version", G + "Before you start, table", cwd="~", expect=r"^Python 3[.](1[1-9]|[2-9][0-9])"),
    SM.run("git-version", "git --version", G + "Before you start, table", cwd="~", expect=r"^git version"),
    SM.run("node-version", "node --version", G + "Before you start, table", cwd="~", expect=r"^v[0-9]+"),
    SM.run("venv", "python3 -m venv ~/outliers-checks", G + "the 3 pytest lines", cwd="~", timeout=300),
    SM.run("pip-pytest", "source ~/outliers-checks/bin/activate && python -m pip install pytest", G + "the 3 pytest lines",
           cwd="~", timeout=600),
    SM.run("pytest-version", "source ~/outliers-checks/bin/activate && python -m pytest --version", G + "the 3 pytest lines",
           cwd="~", expect=r"pytest [0-9]+"),
    SM.run("cd-home", "cd ~", G + "the prompt, before you paste it", cwd="~"),
    SM.run("mkdir", "mkdir my-screen", G + "the prompt, before you paste it", cwd="~", check="test -d ~/my-screen"),
    SM.run("cd-screen", "cd my-screen", G + "the prompt, before you paste it", cwd="~"),
    SM.run("launchctl-list", "launchctl list", G + "starting it by itself, tip", cwd="~", expect=r"PID"),
    SM.run("cd-screen-2", "cd ~/my-screen", G + "when it will not start, step 1", cwd="~"),
    SM.run("cd-home-2", "cd ~", G + "work on a copy", cwd="~"),
    SM.run("copy", "cp -R my-screen my-screen-copy", G + "work on a copy", cwd="~", check="test -d ~/my-screen-copy"),
    SM.run("cd-copy", "cd my-screen-copy", G + "work on a copy", cwd="~"),
]}
