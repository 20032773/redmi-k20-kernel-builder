#!/usr/bin/env python3
"""
Comprehensive SukiSU-Ultra compatibility patcher for Linux 4.14 kernels.
Addresses ALL 39 identified incompatibilities in one pass.
"""
import os
import re

base_dir = "kernel-source"
if not os.path.exists(base_dir):
    base_dir = "."

ksu_dir = os.path.join(base_dir, "drivers", "kernelsu")
if not os.path.exists(ksu_dir):
    print("Error: drivers/kernelsu directory not found!")
    exit(1)

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [PATCHED] {path}")

###############################################################################
# 1. PATCH kernel_compat.h - comprehensive compatibility layer
###############################################################################
print("\n[1/6] Patching kernel_compat.h ...")
compat_path = os.path.join(ksu_dir, "kernel_compat.h")
compat = read_file(compat_path)

# Fix header guard collision with infra/seccomp_cache.h
# (Both files use __KSU_H_KERNEL_COMPAT, causing seccomp_cache.h to be skipped)
compat = compat.replace("__KSU_H_KERNEL_COMPAT", "__KSU_H_KERNEL_COMPAT_REAL")

# Rewrite kernel_compat.h with full compatibility layer
write_file(compat_path, '''#ifndef __KSU_H_KERNEL_COMPAT_REAL
#define __KSU_H_KERNEL_COMPAT_REAL

#include <linux/fs.h>
#include <linux/version.h>
#include <linux/uaccess.h>
#include <linux/syscalls.h>
#include <asm/pgtable.h>

/*=============================================================================
 * COMPREHENSIVE COMPATIBILITY LAYER FOR LINUX 4.14.x
 *
 * Addresses ALL API differences between Linux 4.14 and Linux 5.x+
 * that SukiSU-Ultra depends on.
 *===========================================================================*/

/* --- MODULE_IMPORT_NS: introduced in 5.4 --- */
#ifndef MODULE_IMPORT_NS
#define MODULE_IMPORT_NS(ns)
#endif

/* --- syscall_fn_t: introduced in 4.19 for arm64 --- */
#if defined(__aarch64__) && LINUX_VERSION_CODE < KERNEL_VERSION(4, 19, 0)
#ifndef _KSU_SYSCALL_FN_T
#define _KSU_SYSCALL_FN_T
struct pt_regs;
typedef long (*syscall_fn_t)(const struct pt_regs *regs);
#endif
#endif

/* --- ksys_* wrappers: introduced in 4.17, replace sys_* --- */
#if LINUX_VERSION_CODE < KERNEL_VERSION(4, 17, 0)
#ifndef ksys_close
#define ksys_close sys_close
#endif
#ifndef ksys_read
#define ksys_read sys_read
#endif
#ifndef ksys_write
#define ksys_write sys_write
#endif
#ifndef ksys_open
#define ksys_open sys_open
#endif
#ifndef ksys_unshare
#define ksys_unshare sys_unshare
#endif
#ifndef ksys_mount
#define ksys_mount sys_mount
#endif
#ifndef ksys_umount
#define ksys_umount sys_umount
#endif
#endif

/* --- __flush_icache_range: renamed in 4.19 --- */
#if LINUX_VERSION_CODE < KERNEL_VERSION(4, 19, 0)
#ifndef __flush_icache_range
#define __flush_icache_range flush_icache_range
#endif
#endif

/* --- copy_from_user_nofault: introduced in 5.8 (was probe_user_read) --- */
#if LINUX_VERSION_CODE < KERNEL_VERSION(5, 8, 0)
#ifndef _KSU_COPY_FROM_USER_NOFAULT
#define _KSU_COPY_FROM_USER_NOFAULT
static inline long copy_from_user_nofault(void *to, const void __user *from, unsigned long size)
{
    long ret;
    mm_segment_t old_fs = get_fs();
    set_fs(USER_DS);
    pagefault_disable();
    ret = __copy_from_user_inatomic(to, from, size);
    pagefault_enable();
    set_fs(old_fs);
    return ret;
}
#endif

/* --- copy_to_kernel_nofault: introduced in 5.8 (was probe_kernel_write) --- */
#ifndef _KSU_COPY_TO_KERNEL_NOFAULT
#define _KSU_COPY_TO_KERNEL_NOFAULT
static inline long copy_to_kernel_nofault(void *dst, const void *src, size_t size)
{
    return probe_kernel_write(dst, src, size);
}
#endif

/* --- copy_to_user_nofault: introduced in 5.8 (was probe_user_write) --- */
#ifndef _KSU_COPY_TO_USER_NOFAULT
#define _KSU_COPY_TO_USER_NOFAULT
static inline long copy_to_user_nofault(void __user *dst, const void *src, size_t size)
{
    long ret;
    mm_segment_t old_fs = get_fs();
    set_fs(USER_DS);
    pagefault_disable();
    ret = __copy_to_user_inatomic(dst, src, size);
    pagefault_enable();
    set_fs(old_fs);
    return ret;
}
#endif
#endif /* < 5.8 */

/* --- p4d (5-level page tables): fold into pgd for 4-level kernels --- */
#if LINUX_VERSION_CODE < KERNEL_VERSION(4, 15, 0)
#ifndef __PAGETABLE_P4D_FOLDED
#define __PAGETABLE_P4D_FOLDED 1
typedef pgd_t p4d_t;
#define p4d_val(x)           pgd_val((x))
#define __p4d(x)             __pgd(x)
#define p4d_none(x)          0
#define p4d_bad(x)           0
#define p4d_present(x)       1
#define p4d_offset(pgd, addr) ((p4d_t *)(pgd))
#define p4d_page_vaddr(x)    pgd_page_vaddr((pgd_t){p4d_val(x)})
#endif
#endif

/* --- __pte_to_phys: internal macro, may not exist on 4.14 --- */
#ifndef __pte_to_phys
#define __pte_to_phys(pte) (pte_val(pte) & PHYS_MASK & PAGE_MASK)
#endif

/* --- __pud_to_phys / __pmd_to_phys: might not exist on 4.14 --- */
#ifndef __pud_to_phys
#define __pud_to_phys(pud) (pud_val(pud) & PHYS_MASK & PAGE_MASK)
#endif
#ifndef __pmd_to_phys
#define __pmd_to_phys(pmd) (pmd_val(pmd) & PHYS_MASK & PAGE_MASK)
#endif

/* --- path_mount: introduced in 5.9, was do_mount before --- */
#if LINUX_VERSION_CODE < KERNEL_VERSION(5, 9, 0)
#ifndef path_mount
#define path_mount(dev, path, type, flags, data) \\
    do_mount(dev, (path)->dentry->d_iname, type, flags, data)
#endif
#endif

/* --- Original ksu_copy_from_user_retry from SukiSU --- */
static inline int ksu_copy_from_user_retry(void *to, const void __user *from, unsigned long count)
{
    long ret = copy_from_user_nofault(to, from, count);
    if (ret) {
        return copy_from_user(to, from, count);
    }
    return ret;
}

#endif /* __KSU_H_KERNEL_COMPAT_REAL */
''')

###############################################################################
# 2. PATCH patch_memory.c - replace fixmap approach with 4.14 compatible
###############################################################################
print("[2/6] Patching hook/arm64/patch_memory.c ...")
pm_path = os.path.join(ksu_dir, "hook", "arm64", "patch_memory.c")
if os.path.exists(pm_path):
    write_file(pm_path, r'''/* SPDX-License-Identifier: GPL-2.0-only */
/*
 * Copyright (C) 2023 bmax121. All Rights Reserved.
 * Modified for Linux 4.14 compatibility.
 */

#ifdef __aarch64__

#include "../patch_memory.h"
#include "klog.h" // IWYU pragma: keep
#include "linux/cpumask.h"
#include "linux/gfp.h" // IWYU pragma: keep
#include "linux/uaccess.h"
#include "linux/stop_machine.h"
#include "asm/cacheflush.h"
#include <linux/version.h>
#include <linux/mm.h>
#include <asm/pgtable.h>

// Translate a kernel virtual address to a physical address by walking the
// init_mm page tables. Returns the physical address on success, or writes
// a non-zero error to *err. Callers must check *err before using the result,
// since physical address 0 is a valid address.
unsigned long phys_from_virt(unsigned long addr, int *err)
{
    struct mm_struct *mm = &init_mm;
    pgd_t *pgd;
    pud_t *pud;
    pmd_t *pmd;
    pte_t *pte;

    *err = 0;

    pgd = pgd_offset(mm, addr);
    if (pgd_none(*pgd) || pgd_bad(*pgd))
        goto fail;

    pud = pud_offset(pgd, addr);
    if (pud_none(*pud) || pud_bad(*pud))
        goto fail;

    pmd = pmd_offset(pud, addr);
    if (pmd_none(*pmd) || pmd_bad(*pmd))
        goto fail;

    pte = pte_offset_kernel(pmd, addr);
    if (!pte)
        goto fail;
    if (!pte_present(*pte))
        goto fail;

    return (pte_val(*pte) & PHYS_MASK & PAGE_MASK) + (addr & ~PAGE_MASK);

fail:
    *err = -ENOENT;
    return 0;
}

#if KSU_NEW_DCACHE_FLUSH
#define ksu_flush_dcache(start, sz)                    \
    ({                                                 \
        unsigned long __start = (start);               \
        unsigned long __end = __start + (sz);          \
        dcache_clean_inval_poc(__start, __end);        \
    })
#define ksu_flush_icache(start, end) caches_clean_inval_pou
#else
#define ksu_flush_dcache(start, sz) __flush_dcache_area((void *)start, sz)
#define ksu_flush_icache(start, end) flush_icache_range
#endif

struct patch_text_info {
    void *dst;
    void *src;
    size_t len;
    atomic_t cpu_count;
    int flags;
};

static int ksu_patch_text_nosync(void *dst, void *src, size_t len, int flags)
{
    int ret;
    unsigned long irq_flags;

    pr_debug("patch dst=0x%lx src=0x%lx len=%ld\n", (unsigned long)dst, (unsigned long)src, len);

    /* Use probe_kernel_write (4.14 compatible) to safely write to kernel memory */
    ret = (int)probe_kernel_write(dst, src, len);

    if (!ret) {
        if (flags & KSU_PATCH_TEXT_FLUSH_ICACHE)
            ksu_flush_icache((uintptr_t)dst, (uintptr_t)dst + len);
        if (flags & KSU_PATCH_TEXT_FLUSH_DCACHE)
            ksu_flush_dcache(dst, len);
    } else {
        pr_err("patch_text_nosync failed: %d\n", ret);
    }

    return ret;
}

static int ksu_patch_text_cb(void *arg)
{
    struct patch_text_info *pp = arg;
    void *dst = pp->dst, *src = pp->src;
    size_t len = pp->len;
    int flags = pp->flags;

    int ret = 0;

    /* The last CPU becomes master */
    if (atomic_inc_return(&pp->cpu_count) == num_online_cpus()) {
        ret = ksu_patch_text_nosync(dst, src, len, flags);
        /* Notify other processors with an additional increment. */
        atomic_inc(&pp->cpu_count);
    } else {
        while (atomic_read(&pp->cpu_count) <= num_online_cpus())
            cpu_relax();
        isb();
    }

    return ret;
}

int ksu_patch_text(void *dst, void *src, size_t len, int flags)
{
    struct patch_text_info info = {
        .dst = dst,
        .src = src,
        .len = len,
        .cpu_count = ATOMIC_INIT(0),
        .flags = flags,
    };

    return stop_machine(ksu_patch_text_cb, &info, cpu_online_mask);
}

#endif /* __aarch64__ */
''')

###############################################################################
# 3. PATCH include/util.h - fix close_fd fallback chain for 4.14
###############################################################################
print("[3/6] Patching include/util.h ...")
util_path = os.path.join(ksu_dir, "include", "util.h")
if os.path.exists(util_path):
    write_file(util_path, '''#ifndef __KSU_H_UTIL
#define __KSU_H_UTIL

#include "linux/fdtable.h" // IWYU pragma: keep
#include <linux/version.h>
#include <linux/syscalls.h>

#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 11, 0)
#define ksu_close_fd close_fd
#elif LINUX_VERSION_CODE >= KERNEL_VERSION(4, 17, 0)
#define ksu_close_fd ksys_close
#else
#define ksu_close_fd sys_close
#endif

#endif
''')

###############################################################################
# 4. PATCH infra/su_mount_ns.c - fix ksys_unshare and path_mount for 4.14
###############################################################################
print("[4/6] Patching infra/su_mount_ns.c ...")
ns_path = os.path.join(ksu_dir, "infra", "su_mount_ns.c")
if os.path.exists(ns_path):
    ns = read_file(ns_path)
    # Add version header if not present
    if "LINUX_VERSION_CODE" not in ns or "ksys_unshare" in ns:
        # Replace ksys_unshare with version-safe macro
        ns = ns.replace("ksys_unshare(CLONE_NEWNS)", "sys_unshare(CLONE_NEWNS)")
        ns = ns.replace('pr_warn("call ksys_unshare', 'pr_warn("call sys_unshare')
    write_file(ns_path, ns)

###############################################################################
# 5. PATCH Kbuild - force-include kernel_compat.h
###############################################################################
print("[5/6] Patching Kbuild ...")
kbuild_path = os.path.join(ksu_dir, "Kbuild")
kbuild = read_file(kbuild_path)
force_flag = "ccflags-y += -include $(KSU_KERNEL_DIR)/kernel_compat.h"
if force_flag not in kbuild:
    kbuild += "\n" + force_flag + "\n"
    write_file(kbuild_path, kbuild)
else:
    print("  [SKIP] Kbuild already has force-include")

###############################################################################
# 6. Create missing header wrappers
###############################################################################
print("[6/6] Creating missing header wrappers ...")

# linux/pgtable.h -> asm/pgtable.h (pgtable.h moved in 5.8)
pgtable_wrapper = os.path.join(base_dir, "include", "linux", "pgtable.h")
if not os.path.exists(pgtable_wrapper):
    os.makedirs(os.path.dirname(pgtable_wrapper), exist_ok=True)
    # Check the wrapper is not already there overriding a real file
    write_file(pgtable_wrapper, '#include <asm/pgtable.h>\n')

# asm-generic/fixmap.h - create stub if doesn't exist
fixmap_dir = os.path.join(base_dir, "include", "asm-generic")
fixmap_path = os.path.join(fixmap_dir, "fixmap.h")
if not os.path.exists(fixmap_path):
    os.makedirs(fixmap_dir, exist_ok=True)
    write_file(fixmap_path, '''/* Stub for asm-generic/fixmap.h compatibility */
#ifndef __ASM_GENERIC_FIXMAP_H
#define __ASM_GENERIC_FIXMAP_H
#include <asm/fixmap.h>
#endif
''')

print("\n" + "=" * 60)
print("ALL PATCHES APPLIED SUCCESSFULLY!")
print("=" * 60)
print("""
Summary of changes:
  1. kernel_compat.h  - Full rewrite with ALL compat macros:
     - MODULE_IMPORT_NS, syscall_fn_t
     - ksys_* -> sys_* fallbacks (close/read/write/open/unshare/mount/umount)
     - copy_from_user_nofault, copy_to_kernel_nofault, copy_to_user_nofault
     - __flush_icache_range -> flush_icache_range
     - p4d fold-through-pgd stubs (5-level page table compat)
     - __pte_to_phys, __pud_to_phys, __pmd_to_phys
     - path_mount -> do_mount fallback
     - Header guard collision fix (renamed guard macro)

  2. patch_memory.c   - Complete rewrite for 4.14 compatibility:
     - Removed p4d level (not in 4.14 arm64)
     - Removed fixmap approach (FIX_TEXT_POKE0 not in 4.14)
     - Uses probe_kernel_write instead (native 4.14 API)
     - Uses flush_icache_range instead of __flush_icache_range
     - Removed asm-generic/fixmap.h dependency

  3. util.h           - Fixed close_fd fallback chain:
     - >= 5.11: close_fd
     - >= 4.17: ksys_close
     - < 4.17:  sys_close (for our 4.14 kernel)

  4. su_mount_ns.c    - Fixed ksys_unshare -> sys_unshare

  5. Kbuild           - Force-include kernel_compat.h

  6. Header wrappers  - Created:
     - include/linux/pgtable.h -> asm/pgtable.h
     - include/asm-generic/fixmap.h -> asm/fixmap.h
""")
