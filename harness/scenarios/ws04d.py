"""Jeeves: the Work board panel photographed on a test Mac (wave 6 round 2, 2026-09-25).

The Windows picture panel-board.png shows the PC download link; on a Mac, since e02f829, the panel links
to outliers-ws-03-projectforge-mac. The repo's own tools/shoot.py builds its made-up world (Sam the
bookkeeper) and photographs the panel, headless; here it retakes only panel-board.png into $OUT/shots.
Playwright goes into a private Python folder no member step uses. Never used for a box.
"""
import specs_mac as SM

W = SM.W
REPO = "~/outliers-ws-04-jeeves-mac"

SPEC = {"steps": [
    SM.check("clone", "git clone https://github.com/OUTLIERS-ai/outliers-ws-04-jeeves outliers-ws-04-jeeves-mac && "
             "git -C outliers-ws-04-jeeves-mac log --oneline -1", "the main repo into the -mac folder name", cwd="~",
             timeout=300, ok="any"),
    SM.check("playwright", "python3 -m venv ~/shootvenv && ~/shootvenv/bin/python -m pip install -q playwright && "
             "~/shootvenv/bin/python -m playwright install chromium", "harness only: Playwright for the picture tool",
             cwd="~", timeout=900, ok="any"),
    SM.check("shoot", "mkdir -p \"$OUT/shots\" && ~/shootvenv/bin/python tools/shoot.py ~/shootwork \"$OUT/shots\" panel-board.png; "
             "echo \"=== exit $?\"; ls -la \"$OUT/shots\"", "retake panel-board.png on a Mac", cwd=REPO, timeout=900, ok="any"),
]}
