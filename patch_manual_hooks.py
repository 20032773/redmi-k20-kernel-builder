#!/usr/bin/env python3
"""Finish KernelSU Next manual-hook integration on Linux 4.14.

The pinned coccinelle rules install the classic KernelSU hooks. KernelSU Next
also transports its supercall through reboot(2), and its legacy Kbuild checks
for that call before allowing manual-hook mode.
"""

from pathlib import Path
import sys


ROOT = Path("kernel-source")
if not ROOT.exists():
    ROOT = Path(".")

NAMESPACE = ROOT / "fs" / "namespace.c"
REBOOT = ROOT / "kernel" / "reboot.c"
DECLARATION_MARKER = "/* KernelSU manual-hook forward declarations */"
REBOOT_MARKER = "/* KernelSU Next manual reboot hook */"


def main() -> int:
    if not NAMESPACE.is_file() or not REBOOT.is_file():
        print(f"error: expected {NAMESPACE} and {REBOOT}", file=sys.stderr)
        return 1

    content = NAMESPACE.read_text(encoding="utf-8")
    if DECLARATION_MARKER not in content:
        # The coccinelle hook adds path_umount() near the top of namespace.c.
        # Linux 4.14 defines these helpers later and has no prototypes for them.
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
        print("[+] Added declarations required by manual path_umount hook")
    else:
        print("[*] path_umount declarations are already present")

    reboot = REBOOT.read_text(encoding="utf-8")
    if REBOOT_MARKER not in reboot:
        declaration_target = "static DEFINE_MUTEX(reboot_mutex);"
        syscall_target = """	int ret = 0;

	/* We only trust the superuser with rebooting the system. */"""
        if reboot.count(declaration_target) != 1 or reboot.count(syscall_target) != 1:
            print(
                "error: unexpected kernel/reboot.c layout; refusing a partial hook",
                file=sys.stderr,
            )
            return 1

        declaration = """/* KernelSU Next manual reboot hook */
#ifdef CONFIG_KSU
extern int ksu_handle_sys_reboot(int magic1, int magic2, unsigned int cmd,
				 void __user **arg);
#endif

static DEFINE_MUTEX(reboot_mutex);"""
        syscall = """	int ret = 0;

#ifdef CONFIG_KSU
	ksu_handle_sys_reboot(magic1, magic2, cmd, &arg);
#endif

	/* We only trust the superuser with rebooting the system. */"""
        reboot = reboot.replace(declaration_target, declaration, 1)
        reboot = reboot.replace(syscall_target, syscall, 1)
        REBOOT.write_text(reboot, encoding="utf-8")
        print("[+] Added KernelSU Next manual reboot supercall hook")
    else:
        print("[*] KernelSU Next reboot hook is already present")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
