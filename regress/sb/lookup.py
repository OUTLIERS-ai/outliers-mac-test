# -*- coding: utf-8 -*-
"""Row 23 and row 18 for Parts 2 to 4 on a Mac: with no record of where the second brain is, each
part looks at ~/Second Brain first and still finds one made earlier in ~/Documents/Second Brain;
and nothing it prints tells a Mac member to type `python`.

Used by regress/sb-02, sb-03 and sb-04: `python3 <that test> <part folder>`.
"""
import sys

import sblib as T


def main(needs_layer, extra_args=()):
    if not T.IS_MAC:
        print("SKIPPED: this test is for a Mac only. Windows keeps its look-up order, which the "
              "Windows walk-through proves.")
        sys.exit(3)
    part = T.part_dir()
    py = sys.executable
    argv = [py, "install.py"] + list(extra_args)

    # 1. Only ~/Second Brain, nothing recorded.
    home = T.throwaway_home("lookup-new")
    new = T.make_vault(home / "Second Brain", needs_layer)
    code, out = T.run(argv, part, home)
    T.check("Found your second brain: %s" % new in out, "finds ~/Second Brain with nothing recorded", out[:800])
    T.check(not T.windows_hits(out), "nothing printed is a Windows command or word", T.windows_hits(out))
    T.cleanup(home)

    # 2. Both places: ~/Second Brain first.
    home = T.throwaway_home("lookup-both")
    new = T.make_vault(home / "Second Brain", needs_layer)
    T.make_vault(home / "Documents" / "Second Brain", needs_layer)
    code, out = T.run(argv, part, home)
    T.check("Found your second brain: %s" % new in out, "~/Second Brain is looked at before Documents", out[:800])
    T.cleanup(home)

    # 3. Only Documents (a Mac installed before this fix): still found, never moved.
    home = T.throwaway_home("lookup-old")
    old = T.make_vault(home / "Documents" / "Second Brain", needs_layer)
    code, out = T.run(argv, part, home)
    T.check("Found your second brain: %s" % old in out, "a second brain in Documents is still found", out[:800])
    T.check(not (home / "Second Brain").exists(), "nothing is moved or made at ~/Second Brain")
    T.cleanup(home)

    # 4. None at all: the refusal names the command to type, and it is python3.
    home = T.throwaway_home("lookup-none")
    code, out = T.run(argv, part, home)
    T.check(code == 1 and "cannot find a second brain" in out, "with none, it refuses and changes nothing", out[:800])
    T.check(not T.windows_hits(out), "the refusal prints no Windows command or word", T.windows_hits(out))
    T.cleanup(home)

    T.done()
