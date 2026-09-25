# Picture scenarios (wave 6)

1 file per guide, `<name>.py`, holding `SPEC = {"steps": [...]}` in the same shape as `specs_mac.py`
(it may `import specs_mac as SM` and reuse `SM.prereqs()`, `SM.clone(...)`, `SM.run`, `SM.check`).
Run it with `.github/workflows/mac-scenario.yml` (inputs: `repo` = the `-mac` folder name,
`scenario` = the file name without `.py`). The record keeps every printed output whole, for drawing
a guide's pictures with `Mac-Versions/mac-shots/draw_terminal.py`. It is never a "What was run on a
Mac" record. Each guide writer touches only their own file.
