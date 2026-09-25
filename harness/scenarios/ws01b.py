"""Behaviour check for the agent-flow Mac guide (wave 6 round 2, 2026-09-25): what does pressing Return do
at the installer's 3 questions, with a CRM at ~/CRM (made by CRM layer 1) and with no CRM at all?

Case A: second brain at ~/Second Brain and CRM at ~/CRM (the earlier parts, installed as a member would).
Case B: the CRM and its pointer file moved aside, config.json removed, the installer run again with Return.
Each case prints the questions with their suggestions and the saved config.json.
Record for wording the guide only; never a "What was run on a Mac" record.
"""
import specs_mac as SM

M = "outliers-ws-01-agent-flow-mac"
ANY = "any"
SHOW = "python3 -c \"import json;print(json.dumps(json.load(open('config.json')),indent=1))\""

SPEC = {"steps": SM.prereqs() + [
    SM.check("what-exists", "ls -la ~ | grep -i -E 'crm|second|outliers'; ls ~/CRM | head; cat ~/.outliers-crm ~/.outliers-sb 2>/dev/null",
             "harness: what the earlier parts left in the home folder"),
    SM.clone(M),
    SM.run("install-a", "python3 install.py", "scenario A: Return at every question, CRM at ~/CRM", stdin=SM.ENTER, timeout=900, ok=ANY),
    SM.run("config-a", SHOW, "scenario A: saved answers", ok=ANY),
    SM.run("uninstall-a", "python3 install.py --uninstall", "scenario A: clean up", stdin=SM.ENTER, ok=ANY),
    SM.check("no-crm", "mkdir -p /tmp/aside; mv ~/CRM /tmp/aside/ 2>/dev/null; mv ~/.outliers-crm /tmp/aside/ 2>/dev/null; "
             "rm -f config.json; ls ~ | grep -i crm; echo moved", "harness: take the CRM away"),
    SM.run("install-b", "python3 install.py", "scenario B: Return at every question, no CRM", stdin=SM.ENTER, timeout=900, ok=ANY),
    SM.run("config-b", SHOW, "scenario B: saved answers", ok=ANY),
    SM.run("status-b", "python3 start.py --status", "scenario B", ok=ANY),
    SM.run("uninstall-b", "python3 install.py --uninstall", "scenario B: clean up", stdin=SM.ENTER, ok=ANY),
]}
