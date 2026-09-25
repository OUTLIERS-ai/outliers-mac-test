"""Picture scenario for the FleetView Mac guide (wave 6): the version checks, the install, and the
self-checks through the private Python folder, each with its whole printed output kept."""
import specs_mac as SM

M = "outliers-ws-02-fleetview-mac"
SPEC = {"steps": SM.prereqs() + [
    SM.run("node-version", "node --version", "guide, Before you start", cwd="~"),
    SM.run("python-version", "python3 --version", "guide, Before you start", cwd="~"),
    SM.run("git-version", "git --version", "guide, Before you start", cwd="~"),
    SM.run("python-prefix", "python3 -c \"import sys; print(sys.prefix)\"", "guide, Before you start", cwd="~"),
    SM.clone(M),
    SM.run("install", "python3 install.py", "guide, Install", stdin=SM.ENTER, timeout=900),
    SM.run("status-stop", "python3 install.py --stop", "guide, Install", ok=[0, 1]),
    SM.run("start", "python3 install.py --start", "guide, Install", ok=[0, 1]),
    SM.run("stop-2", "python3 install.py --stop", "guide, Install", ok=[0, 1]),
    SM.run("venv", "python3 -m venv ~/outliers-checks", "guide, self-checks", cwd="~"),
    SM.run("pip-pytest", "source ~/outliers-checks/bin/activate && python -m pip install pytest",
           "guide, self-checks", timeout=600),
    SM.run("npm-test", "npm test", "guide, self-checks", timeout=900),
    SM.run("pytest", "source ~/outliers-checks/bin/activate && python -m pytest -q", "guide, self-checks",
           timeout=1200),
    SM.run("uninstall", "python3 install.py --uninstall", "guide, Install", stdin=SM.ENTER),
]}
