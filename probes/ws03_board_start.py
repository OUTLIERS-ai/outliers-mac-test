"""Probe for fault row 9 (build plan V3): why do 5 ProjectForge tests say the board "never started" on a Mac?

Run from inside a clone of outliers-ws-03-projectforge:  python3 ../_mactest/probes/ws03_board_start.py
It starts the 2 programs those tests start, keeps their whole output, and asks each 3 ways
(Python's urllib as the tests do, a plain socket, and curl), then prints what answered and when.
It checks, in order, the plan's 4 candidates: the wait too short, a command a Mac lacks, the
port still busy, the local-network question.
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


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def by_urllib(port):
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/" % port, timeout=1) as r:
            r.read(1)
        return "ok"
    except Exception as e:  # noqa: BLE001
        return "%s: %s" % (type(e).__name__, e)


def by_socket(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return "ok"
    except OSError as e:
        return "%s: %s" % (type(e).__name__, e)


def by_curl(port):
    r = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "2",
                        "http://127.0.0.1:%d/" % port], capture_output=True, text=True)
    return "http %s (exit %d)" % (r.stdout, r.returncode)


def probe(name, argv, port, env, seconds=40):
    log = Path(tempfile.mkdtemp()) / (name + ".log")
    with open(log, "wb") as fh:
        t0 = time.time()
        p = subprocess.Popen(argv, cwd=str(REPO), env=env, stdout=fh, stderr=subprocess.STDOUT)
        first = {}
        while time.time() - t0 < seconds:
            for how, fn in (("urllib", by_urllib), ("socket", by_socket), ("curl", by_curl)):
                if how not in first and fn(port).startswith(("ok", "http 200", "http 30", "http 404")):
                    first[how] = round(time.time() - t0, 2)
            if len(first) == 3 or p.poll() is not None:
                break
            time.sleep(0.2)
        last = {"urllib": by_urllib(port), "socket": by_socket(port), "curl": by_curl(port)}
        alive = p.poll() is None
        p.kill()
        p.wait(timeout=10)
    print("==== %s: %s" % (name, " ".join(argv)))
    print("still running at the end: %s; exit code: %s" % (alive, p.returncode))
    print("first answer, seconds after start: %s" % json.dumps(first))
    print("last try: %s" % json.dumps(last))
    print("---- its whole output:")
    print(log.read_text(errors="replace")[-4000:] or "(nothing)")
    print()


def main():
    print("python", sys.version.replace("\n", " "), sys.executable)
    print("proxies urllib sees:", urllib.request.getproxies())
    print("proxy env:", {k: v for k, v in os.environ.items() if "proxy" in k.lower()})
    port = free_port()
    probe("http.server", [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], port,
          dict(os.environ))
    tmp = Path(tempfile.mkdtemp())
    cfgp = tmp / "config.json"
    port2 = free_port()
    cfgp.write_text(json.dumps({"summary_note": "", "port": port2, "db_path": "data/forge.db",
                                "hygiene": {"check_every_min": 60}}), encoding="utf-8")
    probe("forge serve", [sys.executable, str(REPO / "forge.py"), "serve", "--port", str(port2)], port2,
          dict(os.environ, FORGE_CONFIG=str(cfgp)))
    print("==== the same, with no proxy settings at all (NO_PROXY=*)")
    port3 = free_port()
    probe("http.server no-proxy", [sys.executable, "-m", "http.server", str(port3), "--bind", "127.0.0.1"],
          port3, dict(os.environ, NO_PROXY="*", no_proxy="*"))


if __name__ == "__main__":
    main()
