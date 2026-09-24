#!/bin/bash
# Clean set-up for the Mac member test (build plan V3, section 9a, as wave 0a changed it):
# a test Mac made like a member's new Mac, with python.org's Python and nodejs.org's Node.js.
#   - the runner's own profile files moved aside; ~/.zshrc starts empty
#   - /etc/paths.d/homebrew and /etc/paths.d/10-pmk-global moved aside (wave 0a M3: GitHub adds
#     them; a member's Mac does not have them), and what was moved is recorded
#   - Intel: Homebrew's Python and Node.js unlinked (wave 0a M2 measured this works)
#   - python.org's package, then its 2 .command files as the test user
#   - nodejs.org's newest LTS package
#   - checks: sys.prefix starts /Library/Frameworks/Python.framework; the real file behind
#     `node` is not Homebrew's. Either check failing stops the job (exit 1).
# Usage: bash setup/clean.sh <out-dir>
OUT="$1"; mkdir -p "$OUT"
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
say "machine"; sw_vers; echo "arch=$ARCH user=$ME image=${ImageOS:-} ${ImageVersion:-}"
empty_profiles
say "runner-only PATH files, moved aside"
sudo mkdir -p /tmp/paths.d-moved-aside
for f in homebrew 10-pmk-global; do
  if [ -e "/etc/paths.d/$f" ]; then sudo mv "/etc/paths.d/$f" /tmp/paths.d-moved-aside/; echo "moved aside: /etc/paths.d/$f"; fi
done
if [ "$ARCH" = "x86_64" ]; then
  say "Intel: unlink Homebrew's Python and Node.js"
  for f in $(brew list --formula | grep -E '^(python@|node)'); do brew unlink "$f"; echo "unlink $f exit $?"; done
fi
install_python_org
hide_runner_python || exit 1
say "nodejs.org LTS package"
NODEVER="$(curl -fsSL https://nodejs.org/dist/index.json | /usr/bin/python3 -c 'import json,sys;print([x["version"] for x in json.load(sys.stdin) if x["lts"]][0])')"
echo "nodejs.org newest LTS: $NODEVER"
curl -fsSL -o /tmp/node.pkg "https://nodejs.org/dist/$NODEVER/node-$NODEVER.pkg"
sudo installer -pkg /tmp/node.pkg -target / ; echo "node installer exit $?"
say "links in /usr/local/bin"
link_list python python3 pip pip3 node npm npx
say "the guide's Python check, in a new Terminal window"
login "$ME" "$PYCHECK"
PFX="$(login "$ME" 'python3 -c "import sys; print(sys.prefix)"' | tail -1)"
NODE_REAL="$(login "$ME" '/usr/bin/python3 -c "import os,shutil;print(os.path.realpath(shutil.which(\"node\") or \"\"))"' | tail -1)"
echo "python3 sys.prefix: $PFX"; echo "node real file: $NODE_REAL"
{ echo "prefix=$PFX"; echo "node=$NODE_REAL"; echo "moved=$(ls /tmp/paths.d-moved-aside 2>/dev/null | tr '\n' ' ')"; } > "$OUT/setup-clean.txt"
case "$PFX" in "$FW"*) ;; *) echo "SET-UP FAILED: python3 is not python.org's"; exit 1;; esac
case "$NODE_REAL" in ""|/usr/local/Cellar/*|/opt/homebrew/*) echo "SET-UP FAILED: node is missing or Homebrew's"; exit 1;; esac
say "clean set-up done"
