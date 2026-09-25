"""Picture scenario for the ProjectForge Mac guide (wave 6, 2026-09-25).

Runs, on 1 test Mac, the situations the ProjectForge Mac guide pictures, so every Mac picture shows
words a program really printed: the checks before you start, an install with no vault (`none` at
question 1), an install with a manager, projects and cards from the terminal, the 3 refusals, the CRM
Today reader, and starting the board a second time. Made-up agents and made-up people only.
Record for drawing pictures only; never a "What was run on a Mac" record.
"""
import specs_mac as SM

M = "outliers-ws-03-projectforge-mac"
ANY = "any"
FORGE = 'forge="$HOME/.claude/projectforge/forge_agent.py"; '
CARD = "C=$(python3 forge.py list | grep -o 'pf-t-[0-9a-f]*' | head -1); echo \"CARD $C\"; "

AGENTS = ("mkdir -p ~/.claude/agents && for a in content-lead writer-bot editor-bot; do "
          "printf -- '---\\nname: %s\\ndescription: made-up agent for the guide pictures\\n---\\nA made-up agent.\\n' \"$a\" "
          "> ~/.claude/agents/$a.md; done; ls ~/.claude/agents")
TODAY = ("mkdir -p ~/CRM/People && printf '# Today\\n\\n| # | Who | Why they are here | When |\\n|---|---|---|---|\\n"
         "| 1 | [[People/Dan Pike]] | Asked about payroll | Call back today |\\n"
         "| 2 | [[Mia Lowe|Mia]] | New connection, runs a design studio | This week |\\n' > ~/CRM/Today.md && "
         "printf '# Dan Pike\\nMade-up person.\\n' > ~/CRM/People/'Dan Pike.md' && "
         "printf '# Mia Lowe\\nMade-up person.\\n' > ~/CRM/People/'Mia Lowe.md' && cat ~/CRM/Today.md")

SPEC = {"steps": SM.prereqs() + [
    SM.run("claude-path", "echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> ~/.zshrc", "scenario", cwd="~"),
    SM.run("v-python", "python3 --version", "scenario", cwd="~"),
    SM.run("v-git", "git --version", "scenario", cwd="~"),
    SM.run("v-claude", "claude --version", "scenario", cwd="~", ok=ANY),
    SM.run("venv", "python3 -m venv ~/outliers-checks", "scenario", cwd="~"),
    SM.run("venv-pytest", "source ~/outliers-checks/bin/activate && python -m pip install pytest", "scenario", cwd="~", timeout=600),
    SM.run("venv-pytest-version", "source ~/outliers-checks/bin/activate && python -m pytest --version", "scenario", cwd="~"),
    SM.clone(M),
    # 1. an install with no vault: `none` at question 1, Enter for the rest
    SM.run("install-novault", "python3 install.py", "scenario", stdin="none\n" + SM.ENTER, timeout=600, ok=ANY),
    SM.run("uninstall-novault", "python3 install.py --uninstall", "scenario", stdin="y\n" + SM.ENTER, ok=ANY),
    SM.check("reset", "rm -f config.json data/forge.db; ls data || true", "harness: back to a fresh download"),
    # 2. made-up agents and a made-up CRM Today page, then an install naming a manager
    SM.check("agents", AGENTS, "harness: 3 made-up agents", cwd="~"),
    SM.check("today", TODAY, "harness: a made-up Today.md with 2 made-up people", cwd="~"),
    SM.run("install", "python3 install.py", "scenario", stdin="\n\n\ncontent-lead\n" + SM.ENTER, timeout=600, ok=ANY),
    # 3. projects and cards from the terminal
    SM.run("add-project", "python3 forge.py add-project \"Content week 39\" --dept content --actor you", "scenario", ok=ANY),
    SM.run("bad-dept", "python3 forge.py add-project \"Launch\" --dept marketing --actor you", "scenario", ok=ANY),
    SM.run("add-tasks", "P=$(python3 forge.py projects | awk 'NR==1{print $1}'); echo \"PROJECT $P\"; "
           "python3 forge.py add-task \"$P\" \"Draft 3 posts\" --status ready --agent writer-bot --actor you; "
           "python3 forge.py add-task \"$P\" \"Tidy the client folder names\" --status ready --actor you", "scenario", ok=ANY),
    SM.run("projects", "python3 forge.py projects", "scenario", ok=ANY),
    SM.run("hygiene", "python3 forge.py hygiene", "scenario", ok=ANY),
    SM.run("list", "python3 forge.py list", "scenario", ok=ANY),
    SM.run("waiting", "python3 forge.py waiting", "scenario", ok=ANY),
    # 4. what the agents run, and the 3 refusals
    SM.run("manager-open", FORGE + "python3 \"$forge\" open --agent content-lead --dept content --project \"Content week 39\" "
           "--title \"Newsletter\" --assignee writer-bot; echo \"exit code $?\"", "scenario", cwd="~", ok=ANY),
    SM.run("worker-open", FORGE + "python3 \"$forge\" open --agent writer-bot --dept content --project \"Content week 39\" "
           "--title \"More posts\"; echo \"exit code $?\"", "scenario", cwd="~", ok=ANY),
    SM.run("worker-move", CARD + "python3 forge.py move \"$C\" done --actor writer-bot; echo \"exit code $?\"", "scenario", ok=ANY),
    SM.run("thin-handoff", CARD + "python3 \"$HOME/.claude/projectforge/forge_agent.py\" handoff --card \"$C\" --from writer-bot "
           "--to editor-bot --done \"handed over\"; echo \"exit code $?\"", "scenario", ok=ANY),
    # 5. the CRM Today reader
    SM.run("crm-dry", "python3 adapters/crm_today.py --dry-run", "scenario", ok=ANY),
    SM.run("crm-real", "python3 adapters/crm_today.py", "scenario", ok=ANY),
    SM.run("crm-again", "python3 adapters/crm_today.py", "scenario", ok=ANY),
    # 6. starting the board a second time, then stopping it
    SM.run("serve-bg", "nohup python3 forge.py serve > /tmp/pf-serve.log 2>&1 & sleep 8; cat /tmp/pf-serve.log", "scenario", ok=ANY, timeout=60),
    SM.run("serve-again", "python3 forge.py serve; echo \"exit code $?\"", "scenario", ok=ANY, timeout=60),
    SM.run("serve-stop", "python3 forge.py serve --stop", "scenario", ok=ANY),
    SM.run("serve-stop-again", "python3 forge.py serve --stop", "scenario", ok=ANY),
    SM.run("make-copy", "python3 forge.py make-copy ../projectforge-practice", "scenario", ok=ANY),
    SM.run("schedule-print", "python3 tools/schedule.py --print", "scenario", ok=ANY),
    SM.run("start-with-computer", "python3 install.py --start-with-computer --yes", "scenario", ok=ANY, timeout=300),
    SM.run("uninstall", "python3 install.py --uninstall", "scenario", stdin="y\n" + SM.ENTER, ok=ANY),
]}
