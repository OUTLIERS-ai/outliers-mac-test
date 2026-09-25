"""Picture and proof scenario for the FleetView Mac guide (wave 6, round 2): the version checks, the install,
the practice copy made exactly as the Mac guide prints it (cp -R, rm -f fleetview.pid, the installer
writing port 3012 with --yes, so no text editor touches config.json), both self-checks run inside the
copy, and the other lines the guide prints in sentences. Every printed output is kept whole."""
import specs_mac as SM

M = "outliers-ws-02-fleetview-mac"
COPY = "~/fleetview-test"
UP12 = "curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://localhost:3012/graph.html | grep -E '^2'"
SPEC = {"steps": SM.prereqs() + [
    SM.run("node-version", "node --version", "guide, Before you start", cwd="~"),
    SM.run("python-version", "python3 --version", "guide, Before you start", cwd="~"),
    SM.run("git-version", "git --version", "guide, Before you start", cwd="~"),
    SM.run("python-prefix", "python3 -c \"import sys; print(sys.prefix)\"", "guide, Before you start", cwd="~"),
    SM.run("ls-projects", "ls ~/.claude/projects", "guide, Before you start", cwd="~", ok="any"),
    SM.clone(M),
    SM.run("install", "python3 install.py", "guide, Install", stdin=SM.ENTER, timeout=900),
    SM.run("stop", "python3 install.py --stop", "guide, Install", ok=[0, 1]),
    SM.run("start", "python3 install.py --start", "guide, Install", ok=[0, 1]),
    SM.run("npm-install", "npm install", "guide, colours (an example of a long command)", timeout=600),
    # The safe way, exactly as printed
    SM.run("copy", "cp -R outliers-ws-02-fleetview-mac fleetview-test", "guide, The safe way 1", cwd="~",
           check="test -f ~/fleetview-test/install.py"),
    SM.run("cd-copy", "cd fleetview-test", "guide, The safe way 1", cwd="~", check="test -d ~/fleetview-test"),
    SM.run("rm-pid", "rm -f fleetview.pid", "guide, The safe way 1", cwd=COPY, check="test ! -e ~/fleetview-test/fleetview.pid"),
    SM.run("port-3012", "python3 install.py --yes --port 3012", "guide, The safe way 1", cwd=COPY, timeout=600,
           check="grep -q '\"port\": 3012' ~/fleetview-test/config.json && cat ~/fleetview-test/config.json"),
    SM.check("everyday-untouched", "grep -q '\"port\": 3010' ~/outliers-ws-02-fleetview-mac/config.json && "
             "curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://localhost:3010/graph.html | grep -E '^2'",
             "the everyday FleetView still has port 3010 and still answers"),
    SM.run("start-copy", "python3 install.py --start", "guide, The safe way 4", cwd=COPY, check=UP12),
    SM.run("venv", "python3 -m venv ~/outliers-checks", "guide, self-checks", cwd="~"),
    SM.run("pip-pytest", "source ~/outliers-checks/bin/activate && python -m pip install pytest",
           "guide, self-checks", cwd=COPY, timeout=600),
    SM.run("npm-test-copy", "npm test", "guide, self-checks in the copy", cwd=COPY, timeout=900),
    SM.run("pytest-copy", "source ~/outliers-checks/bin/activate && python -m pytest -q", "guide, self-checks in the copy",
           cwd=COPY, timeout=1200),
    SM.run("stop-copy", "python3 install.py --stop", "guide, The safe way 4", cwd=COPY, ok=[0, 1]),
    {"id": "port-env", "kind": "serve", "cmd": "PORT=3012 npm start", "url": "http://localhost:3012/graph.html",
     "wait": 40, "cwd": COPY, "source": "guide, Every command and setting", "what": "a setting for 1 start"},
    SM.run("make-demo", "node tools/make-demo.js ~/fleetview-busy-day --sessions 30", "guide, command table",
           check="ls ~/fleetview-busy-day | head"),
    SM.run("cd-back", "cd ../outliers-ws-02-fleetview-mac", "guide, The safe way 5", cwd=COPY,
           check="test -d ~/outliers-ws-02-fleetview-mac"),
    SM.run("stop-2", "python3 install.py --stop", "guide, Install", ok=[0, 1]),
    SM.run("uninstall", "python3 install.py --uninstall", "guide, Install", stdin=SM.ENTER),
    SM.check("launchctl-after-uninstall", "launchctl list | grep -i fleetview; ! launchctl list | grep -q com.outliers.fleetview",
             "after --uninstall the LaunchAgent is no longer loaded (fix 3, ecc3756)"),
]}
