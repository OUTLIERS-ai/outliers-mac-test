# -*- coding: utf-8 -*-
"""Wave 1 second read (push order), Parts 2 to 4: when a part refuses because an earlier part is
missing, it prints the `git clone` and `cd` lines for that part. Those must name a repo that exists,
and switch to the Mac copy (name ending in -mac) with 1 setting, MAC_REPOS_PUBLISHED in install.py:
False until the Mac copies are published (wave 6), True after. Runs on every system.

Used by regress/sb-02, sb-03 and sb-04: `python <that test> <part folder>`.
"""
import re
import shutil
import sys
import tempfile
from pathlib import Path

import sblib as T

PUBLIC = set((T.HARNESS / "public_repos.txt").read_text(encoding="utf-8").split())
SETTING = re.compile(r"(?m)^MAC_REPOS_PUBLISHED\s*=\s*(\w+)\s*$")


def printed_repo(out, name):
    """(clone line names, cd line names) for the part `name`, read off the printed text."""
    clone = re.findall(r"git clone https://github\.com/OUTLIERS-ai/(%s(?:-mac)?)\s*$" % re.escape(name), out, re.M)
    cd = re.findall(r"^\s*cd (%s(?:-mac)?)\s*$" % re.escape(name), out, re.M)
    return clone, cd


def refusal(part, layer):
    home = T.throwaway_home("repo-setting")
    if layer is not None:
        T.make_vault(home / "Documents" / "Second Brain", layer)
    code, out = T.run([sys.executable, "install.py"], part, home)
    T.cleanup(home)
    return code, out


def main(cases):
    part = T.part_dir()
    text = (part / "install.py").read_text(encoding="utf-8")
    T.check(SETTING.findall(text) == ["False"], "install.py sets MAC_REPOS_PUBLISHED exactly once, to False",
            SETTING.findall(text))
    flipped = Path(tempfile.mkdtemp(prefix="sbtest-flipped-")) / part.name
    shutil.copytree(str(part), str(flipped), ignore=shutil.ignore_patterns(".git", "__pycache__"))
    (flipped / "install.py").write_text(SETTING.sub("MAC_REPOS_PUBLISHED = True", text), encoding="utf-8")

    for layer, name in cases:
        where = "no second brain" if layer is None else "a second brain at layer %d" % layer
        T.check(name in PUBLIC, "%s is a published repo" % name)
        code, out = refusal(part, layer)
        T.check(code == 1, "with %s the part refuses" % where, out[:600])
        T.check(printed_repo(out, name) == ([name], [name]),
                "today it prints `git clone .../%s` and `cd %s` (a repo that exists)" % (name, name),
                printed_repo(out, name))
        code, out = refusal(flipped, layer)
        want = name + "-mac" if T.IS_MAC else name
        T.check(printed_repo(out, name) == ([want], [want]),
                "with the 1 line set to True it prints %s on this %s" % (want, "Mac" if T.IS_MAC else "computer"),
                printed_repo(out, name))
    shutil.rmtree(str(flipped.parent), ignore_errors=True)
    T.done()
