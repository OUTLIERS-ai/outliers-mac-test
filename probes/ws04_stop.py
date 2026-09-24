"""Probe for fault row 11 (build plan V3): why does Jeeves' stop test fail on a Mac?

Run from inside a clone of outliers-ws-04-jeeves:  python3 ../_mactest/probes/ws04_stop.py
It builds the made-up demo world, starts Jeeves the way tests/test_fixes.py does (a separate
program, a random port, --config), keeps its whole output, and records when it first answers
(urllib, as the test asks, and curl), what its running record says, and what start.stop() does.
"""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

REPO = Path.cwd()
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def health(port):
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/api/health" % port, timeout=1) as r:
            return "ok " + r.read().decode()[:120]
    except Exception as e:  # noqa: BLE001
        return "%s: %s" % (type(e).__name__, e)


def main():
    import demo
    tmp = Path(tempfile.mkdtemp())
    world = demo.build(tmp / "world")
    state = tmp / "state"
    home = tmp / "home"
    home.mkdir()
    env = dict(os.environ, JEEVES_STATE=str(state), HOME=str(home))
    os.environ.update(JEEVES_STATE=str(state), HOME=str(home))
    port = free_port()
    log = tmp / "jeeves.log"
    t0 = time.time()
    with open(log, "wb") as fh:
        p = subprocess.Popen([sys.executable, str(REPO / "start.py"), "--no-open", "--port", str(port),
                              "--config", str(world)], env=env, stdout=fh, stderr=subprocess.STDOUT)
        first = None
        while time.time() - t0 < 40:
            h = health(port)
            if h.startswith("ok"):
                first = round(time.time() - t0, 2)
                break
            if p.poll() is not None:
                break
            time.sleep(0.2)
        print("python", sys.version.split()[0], sys.executable)
        print("first answer after %s seconds; still running: %s" % (first, p.poll() is None))
        print("last health:", health(port))
        c = subprocess.run(["curl", "-s", "--max-time", "2", "http://127.0.0.1:%d/api/health" % port],
                           capture_output=True, text=True)
        print("curl:", c.stdout[:200], "exit", c.returncode)
        pf = state / "jeeves.pid"
        print("running record %s: %r" % (pf, pf.read_text() if pf.exists() else None))
        import start
        t1 = time.time()
        start.stop(str(world))
        try:
            p.wait(15)
        except subprocess.TimeoutExpired:
            pass
        print("after start.stop(): still running: %s (%.1f s)" % (p.poll() is None, time.time() - t1))
        if p.poll() is None:
            p.kill()
            p.wait(10)
    print("---- Jeeves' whole output:")
    print(log.read_text(errors="replace")[-4000:] or "(nothing)")


if __name__ == "__main__":
    main()
