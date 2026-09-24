#!/bin/bash
# Wave 0a, M6: does a Mac-only test named tests/mac/mac_<name>.py, with no conftest.py beside
# it, leave the plain `python -m pytest -q` counts unchanged on ProjectForge and Jeeves, and is
# it still collected when run by name?
# Usage: bash wave0a/m6.sh <out-dir>
OUT="$1"; mkdir -p "$OUT"
say() { echo; echo "######## $*"; }
python3 -m venv "$HOME/m6venv" && . "$HOME/m6venv/bin/activate"
python -m pip install -q pytest
python --version; python -m pytest --version

probe() {  # $1 = name the repo's tests import from conftest
  cat <<EOF
"""Wave 0a M6 probe. Named outside pytest's default test_*.py pattern on purpose."""
from conftest import $1  # the repo's own tests import conftest by name


def test_mac_probe_is_collected():
    assert $1.exists()
EOF
}

for spec in "outliers-ws-03-projectforge:REPO" "outliers-ws-04-jeeves:ROOT"; do
  REPO="${spec%%:*}"; NAME="${spec##*:}"
  say "$REPO"
  cd "$HOME" && rm -rf "$REPO" && git clone -q "https://github.com/OUTLIERS-ai/$REPO" && cd "$REPO" || continue
  echo "commit $(git rev-parse --short HEAD)"
  echo "--- plain run, before:"; python -m pytest -q -p no:cacheprovider 2>&1 | tail -4
  mkdir -p tests/mac && probe "$NAME" > tests/mac/mac_probe.py
  ls tests/mac
  echo "--- plain run, after adding tests/mac/mac_probe.py:"; python -m pytest -q -p no:cacheprovider 2>&1 | tail -4
  echo "--- collect-only, after (is mac_probe in the list?):"
  python -m pytest -q --collect-only -p no:cacheprovider 2>&1 | grep -c "mac_probe"
  echo "--- by name:"; python -m pytest -q -p no:cacheprovider tests/mac/mac_probe.py 2>&1 | tail -4
  echo "--- by pattern, as the harness will run them:"; python -m pytest -q -p no:cacheprovider tests/mac/mac_*.py 2>&1 | tail -4
done
