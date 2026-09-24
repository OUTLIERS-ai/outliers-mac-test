#!/bin/bash
# Wave 0a, M4: which `python3` answers for a member who already has Homebrew, in each install
# order, and does the guide's fix text bring them to python.org's Python?
#   Order A: Homebrew's PATH line first, then python.org with its profile updater.
#   Order B: python.org with its profile updater first, then Homebrew's PATH line.
# Usage: bash wave0a/homebrew.sh <A|B> <out-dir>
ORDER="$1"; OUT="$2"; mkdir -p "$OUT"
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/lib.sh"
ME="$(id -un)"
ARCH="$(uname -m)"
say "machine"; sw_vers; echo "arch=$ARCH order=$ORDER"
result "machine macos=$(sw_vers -productVersion) arch=$ARCH order=$ORDER"
empty_profiles

PREFIX="$(brew --prefix)"
say "Homebrew as GitHub gives it"
echo "prefix=$PREFIX"; brew --version | head -1
brew list --versions | grep -E '^(python@|node)' || true
if [ ! -x "$PREFIX/bin/python3" ]; then
  echo "Homebrew's python3 not linked; installing it, as a Homebrew member would have"; brew install python
fi
ls -l "$PREFIX/bin/python3"; "$PREFIX/bin/python3" --version
echo "--- /usr/local/bin/python3 before python.org:"; ls -l /usr/local/bin/python3 2>&1

# The line Homebrew's own installer prints under "Next steps" (install.sh, read 2026-09-24):
#   echo 'eval "$(<prefix>/bin/brew shellenv zsh)"' >> ~/.zprofile
if brew shellenv zsh >/dev/null 2>&1; then
  BREWLINE="eval \"\$($PREFIX/bin/brew shellenv zsh)\""
else
  BREWLINE="eval \"\$($PREFIX/bin/brew shellenv)\""
fi
echo "Homebrew PATH line: $BREWLINE"
add_brew_line() { echo >> "$HOME/.zprofile"; echo "$BREWLINE" >> "$HOME/.zprofile"; }

if [ "$ORDER" = "A" ]; then
  say "Order A: Homebrew's line first"
  add_brew_line
  echo "python3 before python.org:"; login "$ME" 'which -a python3; python3 --version'
  install_python_org
else
  say "Order B: python.org first"
  install_python_org
  add_brew_line
fi
echo "--- /usr/local/bin/python3 after python.org:"; ls -l /usr/local/bin/python3 2>&1
echo "--- final ~/.zprofile:"; cat "$HOME/.zprofile"

say "The guide's check in a new Terminal window"
login "$ME" "$PYCHECK"
PFX="$(login "$ME" 'python3 -c "import sys; print(sys.prefix)"' | tail -1)"
case "$PFX" in "$FW"*) CHECK=pass;; *) CHECK=fail;; esac
result "M4 order=$ORDER check_first=$CHECK prefix=$PFX"

if [ "$CHECK" = "fail" ]; then
  say "The guide's fix text: run Update Shell Profile.command again, then a new Terminal window"
  SHELL=/bin/zsh "$PYAPP/Update Shell Profile.command" </dev/null 2>&1 | tail -6
  echo "--- ~/.zprofile after the fix:"; cat "$HOME/.zprofile"
  login "$ME" "$PYCHECK"
  PFX="$(login "$ME" 'python3 -c "import sys; print(sys.prefix)"' | tail -1)"
  case "$PFX" in "$FW"*) CHECK=pass;; *) CHECK=fail;; esac
  result "M4 order=$ORDER check_after_fix=$CHECK prefix=$PFX"
fi

say "python3 -m pip install, as the guide prints it"
login "$ME" 'python3 -m pip install requests' | tail -15; RC=${PIPESTATUS[0]}
result "M4 order=$ORDER pip_exit=$RC"

say "The fallback: the private-folder form gather-04 prints"
login "$ME" 'cd /tmp && python3 -m venv m4venv && source m4venv/bin/activate && python -m pip install requests' | tail -5; RC2=${PIPESTATUS[0]}
result "M4 order=$ORDER private_folder_exit=$RC2"
say "done"
