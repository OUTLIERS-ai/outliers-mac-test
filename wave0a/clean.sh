#!/bin/bash
# Wave 0a, clean set-up job: M3 (login-shell PATH), M2 (Intel only: keeping python.org,
# Homebrew and nodejs.org apart), M1 (python.org Python and `python3 -m pip install` for an
# admin user and a standard user), M5 (is a LaunchAgent refused ~/Documents).
# Usage: bash wave0a/clean.sh <out-dir>
OUT="$1"; mkdir -p "$OUT"
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/lib.sh"
ME="$(id -un)"
ARCH="$(uname -m)"
say "machine"; sw_vers; echo "arch=$ARCH user=$ME uid=$(id -u) image=${ImageOS:-} ${ImageVersion:-}"
result "machine macos=$(sw_vers -productVersion) arch=$ARCH"

# ------------------------------------------------------------------ M3
say "M3: login-shell PATH"
show_macs_path_files
echo "--- login-shell PATH with the runner's own profile files in place:"
login "$ME" 'echo "$PATH"'
empty_profiles
echo "--- login-shell PATH with empty profile files:"
M3PATH="$(login "$ME" 'echo "$PATH"' | tail -1)"
echo "$M3PATH"
result "M3 path=$M3PATH"
STOCK=":/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:"
EXTRA=""
IFS=: read -r -a PARTS <<< "$M3PATH"
for p in "${PARTS[@]}"; do
  case "$STOCK" in *":$p:"*) ;; *) EXTRA="$EXTRA $p";; esac
done
result "M3 extra_folders=[${EXTRA# }]"
echo "--- what those folders hold that matters here:"
for n in python python3 pip pip3 node npm npx brew; do
  printf '%-8s ' "$n"; login "$ME" "command -v $n || echo '(not found)'" | tail -1
done

# ------------------------------------------------------------------ M2 before (Intel only)
if [ "$ARCH" = "x86_64" ]; then
  say "M2 before: /usr/local/bin links, as GitHub gives the Intel Mac"
  link_list python3 pip3 node npm npx
  echo "--- Homebrew formulae present:"; brew list --formula | grep -E '^(python@|node)' || true
  say "M2: brew unlink every python@ and node formula"
  for f in $(brew list --formula | grep -E '^(python@|node)'); do brew unlink "$f"; echo "unlink $f exit $?"; done
  echo "--- after unlink:"; link_list python3 pip3 node npm npx
fi

# ------------------------------------------------------------------ M1 install
install_python_org

if [ "$ARCH" = "x86_64" ]; then
  say "M2: nodejs.org LTS package"
  NODEVER="$(curl -fsSL https://nodejs.org/dist/index.json | /usr/bin/python3 -c 'import json,sys;print([x["version"] for x in json.load(sys.stdin) if x["lts"]][0])')"
  echo "nodejs.org newest LTS: $NODEVER"
  curl -fsSL -o /tmp/node.pkg "https://nodejs.org/dist/$NODEVER/node-$NODEVER.pkg"; echo "download exit $?"
  sudo installer -pkg /tmp/node.pkg -target / ; echo "installer exit $?"
  say "M2 after: /usr/local/bin links"
  link_list python3 pip3 node npm npx | tee /tmp/m2-after.txt
  CELLAR="$(grep -c '/usr/local/Cellar' /tmp/m2-after.txt)"
  result "M2 links_into_homebrew_after=$CELLAR node=$NODEVER"
  if [ "$CELLAR" != "0" ]; then
    say "M2 fallback 1: brew uninstall --ignore-dependencies, then both packages again"
    for f in $(brew list --formula | grep -E '^(python@|node)'); do brew uninstall --ignore-dependencies "$f"; done
    sudo installer -pkg /tmp/python.pkg -target / ; sudo installer -pkg /tmp/node.pkg -target /
    link_list python3 pip3 node npm npx | tee /tmp/m2-fb.txt
    result "M2 fallback1_links_into_homebrew=$(grep -c '/usr/local/Cellar' /tmp/m2-fb.txt)"
  fi
  login "$ME" 'echo "node in a new Terminal window:"; command -v node; node --version; npm --version'
fi

# ------------------------------------------------------------------ M1 admin user
say "M1: the admin test user ($ME), fresh login shell"
dseditgroup -o checkmember -m "$ME" admin
login "$ME" "$PYCHECK"
login "$ME" 'python3 -m pip install requests'; RC=$?
echo "pip exit $RC"
login "$ME" 'python3 -c "import requests; print(\"requests imported from \" + requests.__file__)"'
PFX="$(login "$ME" 'python3 -c "import sys; print(sys.prefix)"' | tail -1)"
result "M1 user=admin prefix=$PFX pip_exit=$RC"

# ------------------------------------------------------------------ M1 standard user
say "M1: a standard (not admin) user made with sysadminctl"
STD="member"
PW="$(openssl rand -hex 16)"
sudo sysadminctl -addUser "$STD" -fullName "Standard Member" -password "$PW" -home "/Users/$STD" 2>&1 | tail -3
sudo createhomedir -c -u "$STD" 2>&1 | tail -2
sudo -u "$STD" touch "/Users/$STD/.zshrc"
dseditgroup -o checkmember -m "$STD" admin
sudo -u "$STD" -H env -i HOME="/Users/$STD" USER="$STD" LOGNAME="$STD" SHELL=/bin/zsh \
  "$PYAPP/Update Shell Profile.command" </dev/null 2>&1 | tail -6
echo "--- the member's ~/.zprofile:"; sudo cat "/Users/$STD/.zprofile" 2>&1
login "$STD" "$PYCHECK"
login "$STD" 'python3 -m pip install requests'; RC2=$?
echo "pip exit $RC2"
login "$STD" 'python3 -c "import requests; print(\"requests imported from \" + requests.__file__)"'
PFX2="$(login "$STD" 'python3 -c "import sys; print(sys.prefix)"' | tail -1)"
result "M1 user=standard prefix=$PFX2 pip_exit=$RC2"

# ------------------------------------------------------------------ M5
say "M5: a LaunchAgent reading ~/Documents and ~/Second Brain"
PYBIN="$FW/Versions/$PYMM/bin/python$PYMM"
DOCS="$HOME/Documents/probe"; SB="$HOME/Second Brain/probe"
mkdir -p "$DOCS" "$SB"; echo "hello from Documents" > "$DOCS/note.md"; echo "hello from Second Brain" > "$SB/note.md"
cat > /tmp/wave0a-probe.py <<'EOF'
import json, os, sys, time
out = sys.argv[1]
res = {"python": sys.executable, "version": sys.version.split()[0], "uid": os.getuid(), "at": time.time()}
for name, d in (("documents", sys.argv[2]), ("second_brain", sys.argv[3])):
    r = {"folder": d}
    try:
        r["listdir"] = sorted(os.listdir(d))
        with open(os.path.join(d, "note.md")) as fh:
            r["read"] = fh.read().strip()
        r["ok"] = True
    except Exception as e:
        r["ok"] = False
        r["error"] = "%s: %s" % (type(e).__name__, e)
    res[name] = r
with open(out, "w") as fh:
    json.dump(res, fh, indent=2)
EOF
LA="$HOME/Library/LaunchAgents"; mkdir -p "$LA"
cat > "$LA/ai.outliers.wave0a.pyprobe.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>ai.outliers.wave0a.pyprobe</string>
  <key>ProgramArguments</key><array>
    <string>$PYBIN</string><string>/tmp/wave0a-probe.py</string><string>/tmp/probe.json</string>
    <string>$DOCS</string><string>$SB</string>
  </array>
  <key>StandardErrorPath</key><string>/tmp/pyprobe.err</string>
</dict></plist>
EOF
cat > "$LA/ai.outliers.wave0a.lsprobe.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>ai.outliers.wave0a.lsprobe</string>
  <key>ProgramArguments</key><array>
    <string>/bin/ls</string><string>-la</string><string>$DOCS</string><string>$SB</string>
  </array>
  <key>StandardOutPath</key><string>/tmp/lsprobe.out</string>
  <key>StandardErrorPath</key><string>/tmp/lsprobe.err</string>
</dict></plist>
EOF
plutil -lint "$LA"/ai.outliers.wave0a.*.plist
for L in pyprobe lsprobe; do
  launchctl bootstrap "gui/$(id -u)" "$LA/ai.outliers.wave0a.$L.plist"; echo "bootstrap $L exit $?"
  launchctl kickstart -k "gui/$(id -u)/ai.outliers.wave0a.$L"; echo "kickstart $L exit $?"
done
sleep 10
screencapture -x "$OUT/m5-screen-$ARCH-$(sw_vers -productVersion).png"; echo "screencapture exit $?"
for L in pyprobe lsprobe; do
  echo "--- launchctl print $L (state and last exit):"
  launchctl print "gui/$(id -u)/ai.outliers.wave0a.$L" | grep -E 'state =|last exit|program ='
done
echo "--- /tmp/probe.json (python.org Python started by launchd):"; cat /tmp/probe.json 2>&1
echo "--- /tmp/pyprobe.err:"; cat /tmp/pyprobe.err 2>&1
echo "--- /tmp/lsprobe.out:"; cat /tmp/lsprobe.out 2>&1
echo "--- /tmp/lsprobe.err:"; cat /tmp/lsprobe.err 2>&1
PYDOC="$(/usr/bin/python3 -c 'import json;d=json.load(open("/tmp/probe.json"));print(d["documents"].get("ok"), d["documents"].get("error",""))' 2>&1)"
PYSB="$(/usr/bin/python3 -c 'import json;d=json.load(open("/tmp/probe.json"));print(d["second_brain"].get("ok"), d["second_brain"].get("error",""))' 2>&1)"
LSERR="$(tr '\n' ' ' < /tmp/lsprobe.err 2>/dev/null)"
result "M5 launchd_python documents_ok=[$PYDOC] second_brain_ok=[$PYSB]"
result "M5 launchd_ls stderr=[$LSERR] stdout_lines=$(wc -l < /tmp/lsprobe.out 2>/dev/null)"
echo "--- control: the same probe run from the shell instead of launchd:"
"$PYBIN" /tmp/wave0a-probe.py /tmp/probe-shell.json "$DOCS" "$SB"; cat /tmp/probe-shell.json
say "M5: what the test Mac's permission databases already grant (read-only look)"
for DB in "/Library/Application Support/com.apple.TCC/TCC.db" "$HOME/Library/Application Support/com.apple.TCC/TCC.db"; do
  echo "--- $DB"
  sudo sqlite3 "$DB" "select service, client, auth_value from access where service like '%Documents%' or service like '%AllFiles%' or service like '%SystemPolicy%' or service like '%ScreenCapture%';" 2>&1 | head -40
done
for L in pyprobe lsprobe; do launchctl bootout "gui/$(id -u)/ai.outliers.wave0a.$L"; rm -f "$LA/ai.outliers.wave0a.$L.plist"; done
cp /tmp/probe.json "$OUT/m5-probe-launchd.json" 2>/dev/null
say "done"
