#!/bin/bash
# Homebrew set-up for the Mac member test (build plan V3, section 9a; wave 0a M4): a member who
# already uses Homebrew. Run once with A, test, then once with B, test again, in the same job.
#   A  Homebrew's own PATH line in ~/.zprofile first (as its installer prints it), then
#      python.org's package and its 2 .command files.
#   B  the same Mac, ~/.zprofile rewritten so python.org's lines come first and Homebrew's line
#      last (the order that failed in wave 0a M4 on Apple Silicon); everything the first member
#      test left in the home folder is moved to /tmp/order-a-leftovers first.
# GitHub's /etc/paths.d/homebrew is moved aside in both: a Homebrew member has the ~/.zprofile
# line instead. The guide's Python check is recorded, not enforced: wave 0a's changed pass line
# is that the guide's words end in a working add-on install either way.
# Usage: bash setup/homebrew.sh <A|B> <out-dir>
ORDER="$1"; OUT="$2"; mkdir -p "$OUT"
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/../wave0a/lib.sh"

# GitHub's image adds a plain `python` (and may add `pip`) inside python.org's own bin folder,
# which python.org's package never installs (found in wave 0b: the first strict run of crm-02
# passed `python install.py` on every Mac because of it). A member's Mac has no such command.
# Every unversioned python/pip/pydoc/idle in any python.org bin folder that no installed package
# owns (pkgutil --file-info names no package) is moved aside and recorded; then a new Terminal
# window must find neither `python` nor `pip`, or the set-up stops.
hide_runner_python() {
  say "plain python and pip commands no installed package owns, moved aside"
  sudo mkdir -p /tmp/runner-python-extras
  local f owner
  for f in /Library/Frameworks/Python.framework/Versions/*/bin/{python,pip,python-config,pydoc,idle} /usr/local/bin/{python,pip}; do
    [ -e "$f" ] || [ -L "$f" ] || continue
    owner="$(pkgutil --file-info "$f" 2>/dev/null | awk '/^pkgid:/{print $2}' | head -1)"
    if [ -n "$owner" ]; then echo "kept (installed by $owner): $f"; continue; fi
    sudo mv "$f" "/tmp/runner-python-extras/$(echo "$f" | tr '/' '_')" && echo "moved aside (no package owns it): $f"
  done
  local found
  found="$(login "$(id -un)" 'command -v python; command -v pip' | grep -v '^$' || true)"
  if [ -n "$found" ]; then echo "SET-UP FAILED: a new Terminal window still finds: $found"; return 1; fi
  echo "a new Terminal window finds no python and no pip, as on a member's Mac"
}
ME="$(id -un)"; ARCH="$(uname -m)"
PREFIX="$(brew --prefix)"
BREWLINE="eval \"\$($PREFIX/bin/brew shellenv zsh)\""
brew shellenv zsh >/dev/null 2>&1 || BREWLINE="eval \"\$($PREFIX/bin/brew shellenv)\""
if [ "$ORDER" = "A" ]; then
  say "Order A: Homebrew's line, then python.org"
  empty_profiles
  sudo mkdir -p /tmp/paths.d-moved-aside
  for f in homebrew 10-pmk-global; do
    if [ -e "/etc/paths.d/$f" ]; then sudo mv "/etc/paths.d/$f" /tmp/paths.d-moved-aside/; echo "moved aside: /etc/paths.d/$f"; fi
  done
  [ -x "$PREFIX/bin/python3" ] || brew install python
  printf '\n%s\n' "$BREWLINE" >> "$HOME/.zprofile"
  install_python_org
  hide_runner_python || exit 1
else
  say "Order B: python.org's lines first, Homebrew's line last; order A's leftovers moved out"
  grep -vF "$BREWLINE" "$HOME/.zprofile" > /tmp/zprofile.b
  printf '\n%s\n' "$BREWLINE" >> /tmp/zprofile.b
  mv /tmp/zprofile.b "$HOME/.zprofile"
  mkdir -p /tmp/order-a-leftovers
  for p in "$HOME"/outliers-* "$HOME/CRM" "$HOME/Documents/Second Brain" "$HOME/Second Brain" "$HOME"/.outliers-*; do
    if [ -e "$p" ]; then mv "$p" /tmp/order-a-leftovers/; echo "moved out: $p"; fi
  done
fi
echo "--- ~/.zprofile:"; cat "$HOME/.zprofile"
say "the guide's Python check, in a new Terminal window"
login "$ME" "$PYCHECK"
PFX="$(login "$ME" 'python3 -c "import sys; print(sys.prefix)"' | tail -1)"
case "$PFX" in "$FW"*) CHECK=pass;; *) CHECK=fail;; esac
echo "order=$ORDER prefix=$PFX check=$CHECK" | tee "$OUT/setup-homebrew-$ORDER.txt"
say "homebrew set-up $ORDER done"
