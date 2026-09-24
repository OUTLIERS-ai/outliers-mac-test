# Shared helpers for the wave 0a measurements (build plan V3, section 11, M1 to M5).
# Sourced by clean.sh and homebrew.sh. No secret, no login, nothing leaves the test Mac
# except the record uploaded at the end of the job.

PYVER="3.14.7"          # newest final release on python.org/ftp/python on 2026-09-24
PYMM="3.14"
PKG_URL="https://www.python.org/ftp/python/$PYVER/python-$PYVER-macos11.pkg"
FW="/Library/Frameworks/Python.framework"
PYAPP="/Applications/Python $PYMM"

say() { echo; echo "######## $*"; }
result() { echo "RESULT $*"; }

home_of() { dscl . -read "/Users/$1" NFSHomeDirectory | awk '{print $2}'; }

# A fresh login shell, as a new Terminal window gives: PATH comes only from the Mac's own
# files (/etc/paths, /etc/paths.d, /etc/zprofile) and the user's profile files.
login() {
  local u="$1"; shift
  local h; h="$(home_of "$u")"
  if [ "$u" = "$(id -un)" ]; then
    env -i HOME="$h" USER="$u" LOGNAME="$u" SHELL=/bin/zsh TERM=xterm-256color \
      /bin/zsh -l -i -c "$*" </dev/null 2>&1
  else
    sudo -u "$u" -H env -i HOME="$h" USER="$u" LOGNAME="$u" SHELL=/bin/zsh TERM=xterm-256color \
      /bin/zsh -l -i -c "cd ~; $*" </dev/null 2>&1
  fi
}

show_macs_path_files() {
  say "the Mac's own PATH files"
  echo "--- /etc/paths"; cat /etc/paths
  for f in /etc/paths.d/*; do echo "--- $f"; cat "$f"; done
  for f in /etc/zshenv /etc/zprofile /etc/zshrc /etc/zlogin; do
    [ -e "$f" ] && { echo "--- $f"; cat "$f"; }
  done
}

# Move the runner's own profile files aside so ~/.zprofile and ~/.zshrc start empty,
# as on a member's new Mac. Each file is printed first so the record shows what was moved.
empty_profiles() {
  say "runner's profile files, moved aside"
  local f
  for f in .zprofile .zshrc .zshenv .zlogin .bash_profile .bashrc .profile; do
    if [ -e "$HOME/$f" ]; then
      echo "--- ~/$f (moved to ~/$f.runner-moved-aside):"; cat "$HOME/$f"
      mv "$HOME/$f" "$HOME/$f.runner-moved-aside"
    else
      echo "--- ~/$f: not present"
    fi
  done
  # An empty ~/.zshrc, as the plan's clean set-up says; it also stops zsh's first-run
  # questions (zsh-newuser-install), which a Mac's Terminal does not show.
  : > "$HOME/.zshrc"
}

link_list() {
  local n
  for n in "$@"; do
    if [ -e "/usr/local/bin/$n" ] || [ -L "/usr/local/bin/$n" ]; then
      printf '%-8s %s  ->  real file: %s\n' "$n" "$(ls -l "/usr/local/bin/$n" | awk '{$1=$2=$3=$4=$5=$6=$7=$8=""; print}' | sed 's/^ *//')" \
        "$(/usr/bin/python3 -c 'import os,sys;print(os.path.realpath(sys.argv[1]))' "/usr/local/bin/$n")"
    else
      printf '%-8s (none in /usr/local/bin)\n' "$n"
    fi
  done
}

install_python_org() {
  say "python.org Python $PYVER: download and install"
  echo "Python framework versions already on this Mac before the install:"
  ls "$FW/Versions" 2>&1
  curl -fsSL -o /tmp/python.pkg "$PKG_URL"; echo "download exit $?"
  shasum -a 256 /tmp/python.pkg
  pkgutil --check-signature /tmp/python.pkg | head -4
  sudo installer -pkg /tmp/python.pkg -target / ; echo "installer exit $?"
  echo "--- ~/.zprofile straight after the installer (did the installer itself change it?):"
  cat "$HOME/.zprofile" 2>&1
  say "Install Certificates.command, as the test user"
  "$PYAPP/Install Certificates.command" </dev/null 2>&1 | tail -8; echo "exit ${PIPESTATUS[0]}"
  say "Update Shell Profile.command, as the test user"
  SHELL=/bin/zsh "$PYAPP/Update Shell Profile.command" </dev/null 2>&1 | tail -12; echo "exit ${PIPESTATUS[0]}"
  echo "--- ~/.zprofile after the profile updater:"; cat "$HOME/.zprofile" 2>&1
}

# The guide's check: which Python answers `python3` in a new Terminal window.
PYCHECK='echo "PATH=$PATH"; echo "which -a python3:"; which -a python3; python3 -c "import sys; print(\"prefix=\" + sys.prefix); print(\"version=\" + sys.version.split()[0])"'
