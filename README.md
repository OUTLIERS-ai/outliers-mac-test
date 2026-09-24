# outliers-mac-test

**This is not something to install.** It is an automatic check of the Outliers member downloads
on real Macs. If you are an Outliers member, you want the repos this one tests, not this one.

## What it does

GitHub lends free Mac computers to public repos. Each time this repo changes, or when someone
presses "Run workflow", it borrows 2 of them:

- `macos-15`: an Apple Silicon (M1) Mac
- `macos-15-intel`: an Intel Mac

On each one it walks through every public Outliers member repo the way a Mac member would:

1. Copies the repo down with `git clone`.
2. Types the install and test commands **exactly as that repo's README or guide prints them**.
   Most of them say `python`, and a Mac has no `python` command, so that usually fails. The
   failure is written down as a finding, not hidden.
3. Tries the obvious Mac replacement (`python3`, `python3 -m pip`, a virtual environment if
   the Mac refuses `pip install`) and writes down which one worked.
4. Runs the repo's own tests and its main command, and checks the promise where a machine can
   check it (a page appears, a file is written, a gate refuses).
5. If the repo sets itself up to start when the Mac logs in, loads that login job with
   `launchctl bootstrap`, checks it runs, then takes it away again.
6. Photographs any web page the repo serves.
7. Runs the repo's uninstall, if it has one, and checks what it left behind.

Every step ends in one of 4 words:

| Word | Meaning |
|---|---|
| WORKS | the command worked exactly as printed |
| WORKS-WITH-SUBSTITUTE | only a Mac replacement worked; the replacement is recorded |
| FAILS | nothing worked |
| NOT-TESTABLE | needs a person's own login (Claude, LinkedIn, Facebook, Fathom), which a borrowed machine must never have |

The record of each run is kept as a download on the run's page: one `.json` and one `.txt`
per repo per Mac, plus the screenshots.

## What it cannot prove

- That a login job survives a real restart. It is loaded by hand, not by restarting.
- A first run on a brand-new Mac. These machines already have Xcode, git and Homebrew, so
  Apple's "install developer tools" box never appears here.
- Anything that needs someone's Claude login. No login is ever used here, and no secret is
  stored in this repo.

## What it does not test

`outliers-content-engine` is private. A public repo cannot copy a private one without a stored
secret, and this repo stores none, so it is left out on purpose.

## Files

| File | What it is |
|---|---|
| `.github/workflows/mac-test.yml` | The run: every repo on both Macs, at most 5 Macs at once |
| `harness/specs.py` | For each repo, the steps a member would take, each copied from that repo's own words |
| `harness/mactest.py` | Runs those steps, tries the Mac replacement when one fails, writes the record |
| `.github/workflows/wave0a.yml` | Wave 0a of the Mac-version build: python.org Python, Homebrew, login-shell PATH, a login job reading `~/Documents`, test-file names, the strict-run rule. Started by hand |
| `.github/workflows/wave0a-m7.yml` | Wave 0a: every repo walked again on 1 Mac with whole outputs kept, plus each program's `--help`, to count Windows words in what the programs print. Started by hand |
| `wave0a/` | The shell scripts those 2 runs use |
| `harness/windows_words.py` | The Windows-word rules, as a scanner with its own self-test |
| `harness/help_sweep.py` | Runs each command-line program in a repo with `--help` and keeps the output |
| `harness/tests/test_strict_no_venv.py` | Proves a strict run (`MACTEST_STRICT=1`) never makes a private Python folder no step made |
| `.github/workflows/mac-versions.yml` | The strict Mac member test on 5 jobs: 3 clean Macs (python.org Python, nodejs.org Node.js, no Homebrew on PATH) and 2 Macs that already have Homebrew, each tried in both install orders. Every step exactly as printed, in a fresh login shell, then every printed output scanned for Windows words. Started by hand |
| `setup/clean.sh`, `setup/homebrew.sh` | The 2 ways a test Mac is made like a member's Mac before that test |
| `harness/check_no_windows.py` | The Windows-word rules (a byte-for-byte copy of the one the Mac versions are built with) |
| `harness/scan_output.py` | Runs those rules over every printed output of a member test |
| `harness/tests/test_login_shell.py` | Proves a login-shell run (`MACTEST_LOGIN=1`) gives each step only what a new Terminal window has |
| `.github/workflows/fix-check.yml`, `fixes/` | Proves a fix from 2 patch files: the new test must fail on the downloaded repo, then pass once the fix is applied, on 3 Macs and Windows. Nothing is pushed anywhere. `fixes/_selftest` proves the workflow itself; `fixes/_selftest-no-red` must fail it |
| `.github/workflows/win-test.yml`, `harness/wintest.py` | The same member steps on GitHub's Windows machine, exactly as printed, in PowerShell |
| `.github/workflows/drift.yml`, `harness/drift.py` | Weekly: is each Mac version still made from its Windows repo's current version? |
| `harness/public_repos.txt` | The 25 public repos; nothing else may be named in a fix |
