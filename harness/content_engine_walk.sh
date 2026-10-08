#!/bin/bash
# Walks the Session 8 content engine guide (Mac edition) on a real Mac, step by step, from the
# public GitHub repo, with Python from python.org as the guide tells a member to install it.
# Each step states the result the guide promises; any other result is a FAIL.
# Then the guide's Homebrew route for carousels (private Python folder) is run as well.
# No secrets, no logins. Output: $1/walk.log and $1/summary.txt, plus the drawn slides.

OUT="${1:-$PWD/out}"
mkdir -p "$OUT"
LOG="$OUT/walk.log"
SUM="$OUT/summary.txt"
: > "$LOG"; : > "$SUM"
FAILS=0

PYVER=3.14.7
FW="/Library/Frameworks/Python.framework/Versions/${PYVER%.*}/bin"

note() { echo "$*" | tee -a "$LOG"; }

# step NAME EXPECTED_EXIT EXPECTED_TEXT -- command...
# EXPECTED_EXIT may be "any"; EXPECTED_TEXT may be "" (no text check).
step() {
  local name="$1" want_code="$2" want_text="$3"; shift 4
  note ""
  note "### $name"
  note "\$ $*"
  local out code
  out="$("$@" 2>&1)"; code=$?
  echo "$out" | tail -40 | tee -a "$LOG"
  local ok=1
  if [ "$want_code" != "any" ] && [ "$code" != "$want_code" ]; then ok=0; fi
  if [ -n "$want_text" ] && ! grep -qF -- "$want_text" <<<"$out"; then ok=0; fi
  if [ $ok = 1 ]; then
    echo "PASS  $name (exit $code)" | tee -a "$LOG" >> "$SUM"
  else
    echo "FAIL  $name (exit $code, wanted $want_code${want_text:+ and text '$want_text'})" | tee -a "$LOG" >> "$SUM"
    FAILS=$((FAILS+1))
  fi
}

note "Mac: $(sw_vers -productVersion) $(uname -m) on ${MAC_LABEL:-unknown runner}"

# --- Before you start: Python from python.org ------------------------------------------------
curl -sSfL -o "$RUNNER_TEMP/python.pkg" "https://www.python.org/ftp/python/$PYVER/python-$PYVER-macos11.pkg"
sudo installer -pkg "$RUNNER_TEMP/python.pkg" -target / >> "$LOG" 2>&1
# The python.org installer's "Update Shell Profile" step puts this folder first on PATH.
export PATH="$FW:$PATH"
step "Python check: python3 --version" 0 "Python $PYVER" -- python3 --version
step "Python check: sys.prefix is python.org's" 0 "/Library/Frameworks/Python.framework" -- \
  python3 -c "import sys; print(sys.prefix)"

# --- Get the kit and prove it runs ------------------------------------------------------------
WORK="$RUNNER_TEMP/member"
mkdir -p "$WORK"; cd "$WORK"
step "Download the kit from the public link" 0 "" -- \
  env GIT_TERMINAL_PROMPT=0 git -c credential.helper= clone -q https://github.com/OUTLIERS-ai/outliers-content-engine.git
cd outliers-content-engine || { echo "FAIL  no kit folder" >> "$SUM"; exit 1; }
note "kit commit: $(git log --oneline -1)"
step "cp config.example.json config.json" 0 "" -- cp config.example.json config.json
step "post_checks on Sam's draft: both planted faults are hard fails" 1 "em dash or en dash present" -- \
  python3 engine/post_checks.py example/briefs/EXAMPLE-WAVE/drafts/EX-01-03-the-vat-account.md
step "post_checks on Sam's draft: the 'not X, it's Y' fault" 1 "'not X, it's Y' reframe" -- \
  python3 engine/post_checks.py example/briefs/EXAMPLE-WAVE/drafts/EX-01-03-the-vat-account.md
step "Review page on Sam's 3 drafts (--open)" 0 "preview ->" -- \
  python3 engine/preview_linkedin.py --dir example/briefs/EXAMPLE-WAVE/drafts --open
step "Review page file exists and names all 3 drafts" 0 "" -- bash -c \
  'f=preview/linkedin-preview.html; test -s $f && grep -q "Sunday" $f && grep -qi "van" $f && grep -qi "vat" $f'
cp preview/linkedin-preview.html "$OUT/" 2>/dev/null

# --- Part 2: mining, before speaker labels are set: must refuse plainly -------------------------
step "mine_transcripts refuses the placeholder speaker label" 1 "my_speaker_labels still holds the placeholder" -- \
  python3 engine/mine_transcripts.py

# --- Part 5: the brief -------------------------------------------------------------------------
step "Copy the template wave to briefs/W01" 0 "" -- cp -R briefs/_TEMPLATE-WAVE briefs/W01
step "Stamp lessons into the W01 brief" 0 "added the lessons block" -- \
  python3 engine/commission_gate.py --stamp briefs/W01/WAVE-COMMISSION.md
step "Gate refuses the unfilled template brief" 1 "NOT BRIEFED" -- \
  python3 engine/commission_gate.py briefs/W01/WAVE-COMMISSION.md
# A filled brief: Sam's, copied out of the example folder.
cp -R example/briefs/EXAMPLE-WAVE briefs/EXW
step "Stamp Sam's filled brief" 0 "lessons block" -- python3 engine/commission_gate.py --stamp briefs/EXW/EX-01-brief.md
step "Gate passes Sam's filled brief" 0 "MAY BE BRIEFED" -- python3 engine/commission_gate.py briefs/EXW/EX-01-brief.md

# --- Part 6: checks ----------------------------------------------------------------------------
step "post_checks on a clean draft of Sam's" any "\"pass\"" -- \
  python3 engine/post_checks.py example/briefs/EXAMPLE-WAVE/drafts/EX-01-01-sunday-night-books.md
step "batch_checks fails Sam's 1-idea wave, as the guide says" 1 "BATCH FAILS" -- \
  python3 engine/batch_checks.py --dir example/briefs/EXAMPLE-WAVE/drafts

# --- Part 8: lessons ---------------------------------------------------------------------------
step "Add the guide's example lesson" 0 "added F0001" -- \
  python3 engine/findings.py add --finding "flat" --action "cut the first line" --evidence "EX-03" --source "W01" --steps hook
step "A lesson with a 3-word action is refused" any "" -- bash -c \
  '! python3 engine/findings.py add --finding "x" --action "be more punchy" --evidence "EX-03" --source "W01" --steps hook'
step "Audit shows the lesson" 0 "1 lessons" -- python3 engine/findings.py audit
step "Gate now refuses Sam's brief until re-stamped" 1 "out of date" -- python3 engine/commission_gate.py briefs/EXW/EX-01-brief.md
step "Re-stamp carries the lesson in" 0 "1 lesson(s)" -- python3 engine/commission_gate.py --stamp briefs/EXW/EX-01-brief.md
step "Gate passes again" 0 "MAY BE BRIEFED" -- python3 engine/commission_gate.py briefs/EXW/EX-01-brief.md

# --- Part 9: provenance ------------------------------------------------------------------------
step "Provenance stamp on a draft" 0 "stamped EX-01-01" -- \
  python3 engine/provenance.py stamp example/briefs/EXAMPLE-WAVE/drafts/EX-01-01-sunday-night-books.md

# --- Carousels, python.org route ---------------------------------------------------------------
step "Carousel set-up: pip install" 0 "" -- python3 -m pip install -q playwright Pillow
step "Carousel set-up: playwright install chromium" 0 "" -- python3 -m playwright install chromium
step "slide_checks with no file prints its help" any "" -- python3 carousel/check/slide_checks.py
for s in list split verdict; do
  step "Build example-$s carousel" 0 "Done." -- python3 carousel/build_carousel.py carousel/specs/example-$s.json
done
mkdir -p "$OUT/slides"; cp carousel/specs/example-*-output/phone/all-slides.png "$OUT/slides/" 2>/dev/null
for f in carousel/specs/example-*-output/phone/all-slides.png; do n=$(basename "$(dirname "$(dirname "$f")")"); cp "$f" "$OUT/slides/$n.png"; done

# --- Carousels, Homebrew route (guide: "written from the code, not run on a Mac") -------------
BREWPY="$(brew --prefix python3 2>/dev/null)/bin/python3"   # Homebrew's own, never python.org's /usr/local/bin link
note "Homebrew python: $BREWPY -> $("$BREWPY" -c "import sys; print(sys.prefix)" 2>&1)"
if [ -x "$BREWPY" ]; then
  step "Homebrew python refuses plain pip (externally-managed-environment)" any "externally-managed-environment" -- \
    "$BREWPY" -m pip install Pillow
  rm -rf "$HOME/carousel-python"
  step "Homebrew route: python3 -m venv ~/carousel-python" 0 "" -- "$BREWPY" -m venv "$HOME/carousel-python"
  step "Homebrew route: pip install in the private folder" 0 "" -- bash -c \
    'source ~/carousel-python/bin/activate && python -m pip install -q playwright Pillow'
  step "Homebrew route: playwright install chromium" 0 "" -- bash -c \
    'source ~/carousel-python/bin/activate && python -m playwright install chromium'
  rm -rf carousel/specs/example-list-output
  step "Homebrew route: build a carousel" 0 "Done." -- bash -c \
    'source ~/carousel-python/bin/activate && python carousel/build_carousel.py carousel/specs/example-list.json'
else
  echo "SKIP  Homebrew route: no Homebrew python3 on this runner" >> "$SUM"
fi

note ""
note "===== SUMMARY ($MAC_LABEL) ====="
cat "$SUM" | tee -a "$LOG"
note "fails: $FAILS"
exit $([ $FAILS = 0 ] && echo 0 || echo 1)
