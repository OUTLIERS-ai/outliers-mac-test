# -*- coding: utf-8 -*-
"""Push order, Part 4: the `git clone` line for Part 3 names a repo that exists and switches to the
Mac copy with 1 setting. See regress/sb/repo_setting.py. Every system.

    python test_repo_setting.py <part folder>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sb"))
import repo_setting  # noqa: E402

repo_setting.main([(2, "outliers-sb-03-capture")])
