#!/usr/bin/env python3
"""Fix declarations required by KernelSU coccinelle hooks on Linux 4.14."""

from pathlib import Path
import sys


ROOT = Path("kernel-source")
if not ROOT.exists():
    ROOT = Path(".")

NAMESPACE = ROOT / "fs" / "namespace.c"
DECLARATION_MARKER = "/* KernelSU manual-hook forward declarations */"


def main() -> int:
    if not NAMESPACE.is_file():
        print(f"error: {NAMESPACE} was not found", file=sys.stderr)
        return 1

    content = NAMESPACE.read_text(encoding="utf-8")
    if DECLARATION_MARKER in content:
        print("[*] KernelSU manual-hook declarations are already present")
        return 0

    # The coccinelle hook adds path_umount() near the top of namespace.c.
    # Linux 4.14 defines these helpers much later and has no prototypes for
    # them, so Clang first infers external declarations and then rejects their
    # real static definitions.  Keep the signatures identical to this tree.
    target = "static inline struct hlist_head *mp_hash"
    if content.count(target) != 1:
        print(
            "error: expected one mp_hash insertion point in fs/namespace.c, "
            f"found {content.count(target)}",
            file=sys.stderr,
        )
        return 1

    declarations = """/* KernelSU manual-hook forward declarations */
static inline bool may_mount(void);
static inline int check_mnt(struct mount *mnt);
static int do_umount(struct mount *mnt, int flags);
static void mntput_no_expire(struct mount *mnt);

static inline struct hlist_head *mp_hash"""
    content = content.replace(target, declarations, 1)
    NAMESPACE.write_text(content, encoding="utf-8")
    print("[+] Added Linux 4.14 declarations required by manual path_umount hook")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
