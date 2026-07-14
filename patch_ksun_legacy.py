#!/usr/bin/env python3
"""Apply strict KernelSU Next legacy compatibility fixes for this 4.14 tree."""

from pathlib import Path
import sys


ROOT = Path("kernel-source")
if not ROOT.exists():
    ROOT = Path(".")

EVENT = ROOT / "drivers" / "kernelsu" / "sulog" / "event.c"
EVENT_QUEUE = ROOT / "drivers" / "kernelsu" / "infra" / "event_queue.h"
LINUX_TYPES = ROOT / "include" / "uapi" / "linux" / "types.h"

TIMESPEC_MARKER = "Redmi K20 Linux 4.14 boottime type compatibility"
POLL_MARKER = "Redmi K20 vendor kernel already defines __poll_t"


def patch_timespec() -> None:
    source = EVENT.read_text(encoding="utf-8")
    if source.count(TIMESPEC_MARKER) == 2:
        print("[*] KernelSU Next SULog boottime types are already patched")
        return

    old = "    struct timespec64 ts;"
    if source.count(old) != 2:
        raise RuntimeError(
            "SULog timespec declarations: expected exactly two upstream matches, "
            f"found {source.count(old)}"
        )

    new = """    /* Redmi K20 Linux 4.14 boottime type compatibility */
#if KERNEL_VERSION(4, 19, 0) <= LINUX_VERSION_CODE
    struct timespec64 ts;
#else
    struct timespec ts;
#endif"""
    EVENT.write_text(source.replace(old, new), encoding="utf-8")
    print("[+] Patched KernelSU Next SULog boottime types for Linux 4.14")


def patch_poll_type() -> None:
    queue = EVENT_QUEUE.read_text(encoding="utf-8")
    types = LINUX_TYPES.read_text(encoding="utf-8")
    if POLL_MARKER in queue:
        print("[*] KernelSU Next __poll_t compatibility is already patched")
        return

    # This vendor 4.14 tree backports __poll_t in linux/types.h. KernelSU
    # Next's version-only fallback would typedef it a second time.
    if "typedef unsigned __poll_t;" not in types:
        print("[*] Target kernel does not backport __poll_t; keeping fallback")
        return

    old = """#include <linux/version.h>
#if LINUX_VERSION_CODE < KERNEL_VERSION(4, 16, 0)
typedef unsigned int __poll_t;
#endif"""
    if queue.count(old) != 1:
        raise RuntimeError(
            "event_queue __poll_t fallback: expected exactly one upstream match, "
            f"found {queue.count(old)}"
        )

    new = """#include <linux/version.h>
/* Redmi K20 vendor kernel already defines __poll_t in linux/types.h. */"""
    EVENT_QUEUE.write_text(queue.replace(old, new, 1), encoding="utf-8")
    print("[+] Removed duplicate KernelSU Next __poll_t typedef")


def main() -> int:
    missing = [path for path in (EVENT, EVENT_QUEUE, LINUX_TYPES) if not path.is_file()]
    if missing:
        print("error: missing required files: " + ", ".join(map(str, missing)), file=sys.stderr)
        return 1

    try:
        patch_timespec()
        patch_poll_type()
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
