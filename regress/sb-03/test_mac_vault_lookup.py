# -*- coding: utf-8 -*-
"""Rows 23 and 18, Part 3: on a Mac the part finds ~/Second Brain first, still finds one in
~/Documents/Second Brain, and prints python3, never python. See regress/sb/lookup.py.

    python3 test_mac_vault_lookup.py <part folder>      # on a Mac; elsewhere SKIPPED, exit 3
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sb"))
import lookup  # noqa: E402

lookup.main(needs_layer=2)
