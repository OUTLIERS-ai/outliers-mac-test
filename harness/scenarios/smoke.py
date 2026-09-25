"""Smoke test of the scenario mode: 1 printed-output step, no member repo."""
import specs_mac as SM

SPEC = {"steps": [SM.run("hello", "python3 --version; node --version; echo scenario-ok", "smoke", cwd="~")]}
