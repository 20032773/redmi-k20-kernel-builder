#!/usr/bin/env python3
"""Avoid Linux 4.14 Kbuild's oversized ThinLTO archive command.

CONFIG_MODVERSIONS expands the composite object's prerequisite list once for
symbol-version collection and again for llvm-ar.  qcacld's object list is large
enough that the resulting `/bin/sh -c` argument exceeds MAX_ARG_STRLEN.  Have
GNU make write the first copy to a response file before it invokes the shell.
"""

from pathlib import Path


path = Path("scripts/Makefile.build")
text = path.read_text()

definition = "  update_lto_symversions ="
old_loop = "\tfor i in $(filter-out FORCE,$^); do"
new_loop = "\t$(file >$@.lto-prereqs,$(filter-out FORCE,$^)) \\\n\tfor i in $$(cat $@.lto-prereqs); do"

if text.count(definition) != 1:
    raise SystemExit("unexpected update_lto_symversions definition count")
if text.count(old_loop) != 1:
    raise SystemExit("unexpected ThinLTO prerequisite loop count")

path.write_text(text.replace(old_loop, new_loop, 1))

patched = path.read_text()
if patched.count("$@.lto-prereqs") != 2:
    raise SystemExit("ThinLTO prerequisite response-file patch verification failed")
