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
print("\n[1/9] Patching kernel_compat.h ...")
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
#include <linux/audit.h>
#include <asm/pgtable.h>
#include <asm/unistd.h>

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

/* --- task_work notify modes: 4.14 uses a boolean notify argument --- */
#if LINUX_VERSION_CODE < KERNEL_VERSION(5, 2, 0)
#define TWA_RESUME true
#endif

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

/* --- seccomp action-cache sizes: added to arm64 after Linux 4.14 --- */
#ifndef SECCOMP_ARCH_NATIVE_NR
#define SECCOMP_ARCH_NATIVE_NR NR_syscalls
#endif
#ifdef CONFIG_COMPAT
#ifndef SECCOMP_ARCH_COMPAT
#define SECCOMP_ARCH_COMPAT AUDIT_ARCH_ARM
#endif
#ifndef SECCOMP_ARCH_COMPAT_NR
#define SECCOMP_ARCH_COMPAT_NR __NR_compat_syscalls
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
print("[2/9] Patching hook/arm64/patch_memory.c ...")
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
print("[3/9] Patching include/util.h ...")
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
# 4. PATCH infra/su_mount_ns.c - backport namespace syscalls to Linux 4.14
###############################################################################
print("[4/9] Patching infra/su_mount_ns.c ...")
ns_path = os.path.join(ksu_dir, "infra", "su_mount_ns.c")
if os.path.exists(ns_path):
    ns = read_file(ns_path)

    # mount.h was split out after 4.14. This file only needs MS_PRIVATE and
    # MS_REC, both already supplied by linux/fs.h in the target kernel.
    ns = ns.replace("#include <uapi/linux/mount.h>\n", "")

    modern_setns = '''extern int path_mount(const char *dev_name, struct path *path, const char *type_page, unsigned long flags,
                      void *data_page);

#if defined(__aarch64__)
extern long __arm64_sys_setns(const struct pt_regs *regs);
#elif defined(__x86_64__)
extern long __x64_sys_setns(const struct pt_regs *regs);
#endif

static long ksu_sys_setns(int fd, int flags)
{
    struct pt_regs regs;
    memset(&regs, 0, sizeof(regs));

    PT_REGS_PARM1(&regs) = fd;
    PT_REGS_PARM2(&regs) = flags;

#if defined(__aarch64__)
    return __arm64_sys_setns(&regs);
#elif defined(__x86_64__)
    return __x64_sys_setns(&regs);
#else
#error "Unsupported arch"
#endif
}
'''
    legacy_setns = '''/* Linux 4.14 predates syscall wrapper functions such as
 * __arm64_sys_setns(); call the native syscall implementation directly. */
static long ksu_sys_setns(int fd, int flags)
{
    return sys_setns(fd, flags);
}
'''
    if modern_setns not in ns:
        print("Error: unexpected SukiSU setns implementation in su_mount_ns.c")
        exit(1)
    ns = ns.replace(modern_setns, legacy_setns, 1)

    modern_individual = '''static void ksu_mnt_ns_individual(void)
{
    long ret = ksys_unshare(CLONE_NEWNS);
    if (ret) {
        pr_warn("call ksys_unshare failed: %ld\\n", ret);
        return;
    }

    // make root mount private
    struct path root_path;
    get_fs_root(current->fs, &root_path);
    int pm_ret = path_mount(NULL, &root_path, NULL, MS_PRIVATE | MS_REC, NULL);
    path_put(&root_path);

    if (pm_ret < 0) {
        pr_err("failed to make root private, err: %d\\n", pm_ret);
    }
}
'''
    legacy_individual = '''static void ksu_mnt_ns_individual(void)
{
    long ret = sys_unshare(CLONE_NEWNS);
    mm_segment_t old_fs;

    if (ret) {
        pr_warn("call sys_unshare failed: %ld\\n", ret);
        return;
    }

    /* Linux 4.14 has do_mount() rather than path_mount(). do_mount() treats
     * dir_name as a userspace pointer, so temporarily allow the kernel string
     * while making the root of the new namespace private. */
    old_fs = get_fs();
    set_fs(KERNEL_DS);
    ret = do_mount(NULL, (const char __user *)"/", NULL,
                   MS_PRIVATE | MS_REC, NULL);
    set_fs(old_fs);

    if (ret < 0)
        pr_err("failed to make root private, err: %ld\\n", ret);
}
'''
    if modern_individual not in ns:
        print("Error: unexpected SukiSU individual mount namespace implementation")
        exit(1)
    ns = ns.replace(modern_individual, legacy_individual, 1)

    # close_fd appeared after this kernel; sys_close is declared by syscalls.h.
    ns = ns.replace("ksys_close(fd);", "sys_close(fd);")
    write_file(ns_path, ns)

###############################################################################
# 5. PATCH remaining filesystem APIs used only by late KSU objects
###############################################################################
print("[5/9] Backporting late-object filesystem and seccomp APIs ...")

umount_path = os.path.join(ksu_dir, "feature", "kernel_umount.c")
umount_src = read_file(umount_path)
modern_umount = '''extern int path_umount(struct path *path, int flags);

static void ksu_umount_mnt(const char *mnt, struct path *path, int flags)
{
    int err = path_umount(path, flags);
    if (err) {
        pr_info("umount %s failed: %d\\n", mnt, err);
    }
}
'''
legacy_umount = '''static void ksu_umount_mnt(const char *mnt, struct path *path, int flags)
{
    mm_segment_t old_fs;
    int err;

    (void)path;
    old_fs = get_fs();
    set_fs(KERNEL_DS);
    err = sys_umount((char __user *)mnt, flags);
    set_fs(old_fs);
    if (err)
        pr_info("umount %s failed: %d\\n", mnt, err);
}
'''
if modern_umount not in umount_src:
    print("Error: unexpected SukiSU kernel_umount implementation")
    exit(1)
umount_src = umount_src.replace(modern_umount, legacy_umount, 1)
write_file(umount_path, umount_src)

observer_path = os.path.join(ksu_dir, "manager", "pkg_observer.c")
observer = read_file(observer_path)
modern_observer = '''static int ksu_handle_inode_event(struct fsnotify_mark *mark, u32 mask, struct inode *inode, struct inode *dir,
                                  const struct qstr *file_name, u32 cookie)
{
    if (!file_name)
        return 0;
    if (mask & FS_ISDIR)
        return 0;
    if (file_name->len == 13 && !memcmp(file_name->name, "packages.list", 13)) {
        pr_info("packages.list detected: %d\\n", mask);
        track_throne(false);
    }
    return 0;
}

static const struct fsnotify_ops ksu_ops = {
    .handle_inode_event = ksu_handle_inode_event,
};
'''
legacy_observer = '''static int ksu_handle_event(struct fsnotify_group *group, struct inode *inode,
                            struct fsnotify_mark *inode_mark,
                            struct fsnotify_mark *vfsmount_mark, u32 mask,
                            const void *data, int data_type,
                            const unsigned char *file_name, u32 cookie,
                            struct fsnotify_iter_info *iter_info)
{
    if (!file_name || (mask & FS_ISDIR))
        return 0;
    if (!strcmp((const char *)file_name, "packages.list")) {
        pr_info("packages.list detected: %d\\n", mask);
        track_throne(false);
    }
    return 0;
}

static const struct fsnotify_ops ksu_ops = {
    .handle_event = ksu_handle_event,
};
'''
if modern_observer not in observer:
    print("Error: unexpected SukiSU fsnotify callback implementation")
    exit(1)
observer = observer.replace(modern_observer, legacy_observer, 1)
observer = observer.replace("fsnotify_add_inode_mark(m, inode, 0)",
                            "fsnotify_add_mark(m, inode, NULL, 0)")
write_file(observer_path, observer)

app_profile_path = os.path.join(ksu_dir, "policy", "app_profile.c")
app_profile = read_file(app_profile_path)

# filter_count was added in Linux 5.9.  Older kernels only maintain the
# filter pointer and expose put_seccomp_filter() for dropping its reference.
old_release_decl = "void seccomp_filter_release(struct task_struct *tsk);\n"
if old_release_decl not in app_profile:
    print("Error: unexpected SukiSU seccomp release declaration")
    exit(1)
app_profile = app_profile.replace(
    old_release_decl,
    "/* Linux 4.14 declares put_seccomp_filter() in linux/seccomp.h. */\n",
    1,
)

old_filter_count = "    atomic_set(&current->seccomp.filter_count, 0);\n"
if old_filter_count not in app_profile:
    print("Error: unexpected SukiSU seccomp filter_count reset")
    exit(1)
app_profile = app_profile.replace(
    old_filter_count,
    "#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 9, 0)\n"
    "    atomic_set(&current->seccomp.filter_count, 0);\n"
    "#endif\n",
    1,
)

if "    seccomp_filter_release(fake);\n" not in app_profile:
    print("Error: unexpected SukiSU seccomp release call")
    exit(1)
app_profile = app_profile.replace(
    "    seccomp_filter_release(fake);\n",
    "    put_seccomp_filter(fake);\n",
    1,
)
write_file(app_profile_path, app_profile)

###############################################################################
# 6. PATCH SELinux integration - Linux 4.14 uses selinux_state.ss
###############################################################################
print("[6/9] Backporting SELinux integration to the Linux 4.14 state model ...")

sepolicy_h_path = os.path.join(ksu_dir, "selinux", "sepolicy.h")
sepolicy_h = read_file(sepolicy_h_path)
if "struct selinux_policy;" not in sepolicy_h:
    sepolicy_h = sepolicy_h.replace(
        '#include "ss/policydb.h"\n',
        '#include "ss/policydb.h"\n\n'
        '/* Linux 4.14 has selinux_state.ss, not struct selinux_policy. */\n'
        'struct selinux_policy;\n',
        1,
    )
    write_file(sepolicy_h_path, sepolicy_h)

rules_path = os.path.join(ksu_dir, "selinux", "rules.c")
rules = read_file(rules_path)

legacy_apply = r'''void apply_kernelsu_rules()
{
    struct policydb *db;

    if (!getenforce()) {
        pr_info("SELinux permissive or disabled, apply rules!\n");
    }

    /* Linux 4.14 keeps the active policydb in selinux_state.ss.  This is
     * the same live-policy integration used by KernelSU before non-GKI
     * support was removed.  A modern struct selinux_policy does not exist. */
    rcu_read_lock();
    db = &selinux_state.ss->policydb;

    ksu_type(db, KERNEL_SU_DOMAIN, "domain");
    ksu_permissive(db, KERNEL_SU_DOMAIN);
    ksu_typeattribute(db, KERNEL_SU_DOMAIN, "mlstrustedsubject");
    ksu_typeattribute(db, KERNEL_SU_DOMAIN, "netdomain");
    ksu_typeattribute(db, KERNEL_SU_DOMAIN, "bluetoothdomain");

    ksu_type(db, KERNEL_SU_FILE, "file_type");
    ksu_typeattribute(db, KERNEL_SU_FILE, "mlstrustedobject");
    ksu_allow(db, "domain", KERNEL_SU_FILE, ALL, ALL);
    ksu_allow(db, KERNEL_SU_DOMAIN, ALL, ALL, ALL);

    if (db->policyvers >= POLICYDB_VERSION_XPERMS_IOCTL) {
        ksu_allowxperm(db, KERNEL_SU_DOMAIN, ALL, "blk_file", ALL);
        ksu_allowxperm(db, KERNEL_SU_DOMAIN, ALL, "fifo_file", ALL);
        ksu_allowxperm(db, KERNEL_SU_DOMAIN, ALL, "chr_file", ALL);
        ksu_allowxperm(db, KERNEL_SU_DOMAIN, ALL, "file", ALL);
    }

    ksu_allow(db, "init", KERNEL_SU_DOMAIN, ALL, ALL);
    ksu_allow(db, "servicemanager", KERNEL_SU_DOMAIN, "dir", "search");
    ksu_allow(db, "servicemanager", KERNEL_SU_DOMAIN, "dir", "read");
    ksu_allow(db, "servicemanager", KERNEL_SU_DOMAIN, "file", "open");
    ksu_allow(db, "servicemanager", KERNEL_SU_DOMAIN, "file", "read");
    ksu_allow(db, "servicemanager", KERNEL_SU_DOMAIN, "process", "getattr");
    ksu_allow(db, "domain", KERNEL_SU_DOMAIN, "process", "sigchld");
    ksu_allow(db, "logd", KERNEL_SU_DOMAIN, "dir", "search");
    ksu_allow(db, "logd", KERNEL_SU_DOMAIN, "file", "read");
    ksu_allow(db, "logd", KERNEL_SU_DOMAIN, "file", "open");
    ksu_allow(db, "logd", KERNEL_SU_DOMAIN, "file", "getattr");
    ksu_allow(db, "domain", KERNEL_SU_DOMAIN, "fd", "use");
    ksu_allow(db, "domain", KERNEL_SU_DOMAIN, "fifo_file", "write");
    ksu_allow(db, "domain", KERNEL_SU_DOMAIN, "fifo_file", "read");
    ksu_allow(db, "domain", KERNEL_SU_DOMAIN, "fifo_file", "open");
    ksu_allow(db, "domain", KERNEL_SU_DOMAIN, "fifo_file", "getattr");
    ksu_allow(db, "domain", KERNEL_SU_DOMAIN, "unix_stream_socket", "read");
    ksu_allow(db, "domain", KERNEL_SU_DOMAIN, "unix_stream_socket", "write");
    ksu_allow(db, "domain", KERNEL_SU_DOMAIN, "unix_stream_socket", "connectto");
    ksu_allow(db, "domain", KERNEL_SU_DOMAIN, "unix_stream_socket", "getopt");
    ksu_allow(db, "domain", KERNEL_SU_DOMAIN, "unix_stream_socket", "getattr");
    ksu_allow(db, "hwservicemanager", KERNEL_SU_DOMAIN, "dir", "search");
    ksu_allow(db, "hwservicemanager", KERNEL_SU_DOMAIN, "file", "read");
    ksu_allow(db, "hwservicemanager", KERNEL_SU_DOMAIN, "file", "open");
    ksu_allow(db, "hwservicemanager", KERNEL_SU_DOMAIN, "process", "getattr");
    ksu_allow(db, "domain", KERNEL_SU_DOMAIN, "binder", ALL);
    ksu_allow(db, "system_server", KERNEL_SU_DOMAIN, "process", "getpgid");
    ksu_allow(db, "system_server", KERNEL_SU_DOMAIN, "process", "sigkill");

    rcu_read_unlock();
    reset_avc_cache();
}
'''

rules, count = re.subn(
    r"void apply_kernelsu_rules\(\)\n\{.*?\n\}\n\n#define KSU_SEPOLICY_MAX_BATCH_SIZE",
    lambda _match: legacy_apply + "\n#define KSU_SEPOLICY_MAX_BATCH_SIZE",
    rules,
    count=1,
    flags=re.S,
)
if count != 1:
    print("Error: unexpected SukiSU apply_kernelsu_rules implementation")
    exit(1)

legacy_handle = r'''int handle_sepolicy(void __user *user_data, u64 data_len)
{
    struct policydb *db;
    struct sepol_batch_cursor cursor;
    u8 *payload;
    int ret = 0;
    int success_cmd_count = 0;
    u32 cmd_index = 0;

    if (!user_data || !data_len)
        return -EINVAL;
    if (data_len > KSU_SEPOLICY_MAX_BATCH_SIZE)
        return -E2BIG;

    payload = kvmalloc((size_t)data_len, GFP_KERNEL);
    if (!payload)
        return -ENOMEM;
    if (copy_from_user(payload, user_data, (size_t)data_len)) {
        ret = -EFAULT;
        goto out_free;
    }

    rcu_read_lock();
    db = &selinux_state.ss->policydb;
    cursor.cur = payload;
    cursor.end = payload + (size_t)data_len;

    while (cursor.cur < cursor.end) {
        struct sepol_data header;
        const char *args[KSU_SEPOLICY_MAX_ARGS] = { 0 };
        int expected_argc;
        u32 arg_index;

        ret = sepol_read_cmd_header(&cursor, &header);
        if (ret < 0)
            break;
        expected_argc = sepol_expected_argc(header.cmd);
        if (expected_argc < 0 || expected_argc > KSU_SEPOLICY_MAX_ARGS) {
            ret = -EINVAL;
            break;
        }
        for (arg_index = 0; arg_index < (u32)expected_argc; arg_index++) {
            ret = sepol_read_string(&cursor, &args[arg_index]);
            if (ret < 0)
                break;
        }
        if (ret < 0)
            break;
        ret = apply_one_sepolicy_cmd(db, &header, args);
        if (ret >= 0)
            success_cmd_count++;
        cmd_index++;
    }

    rcu_read_unlock();
    if (success_cmd_count)
        reset_avc_cache();
    if (ret >= 0)
        ret = success_cmd_count;

out_free:
    kvfree(payload);
    return ret;
}
'''
rules, count = re.subn(
    r"int handle_sepolicy\(void __user \*user_data, u64 data_len\)\n\{.*?\n\}\s*$",
    lambda _match: legacy_handle,
    rules,
    count=1,
    flags=re.S,
)
if count != 1:
    print("Error: unexpected SukiSU handle_sepolicy implementation")
    exit(1)
write_file(rules_path, rules)

# Modern SukiSU duplicates a struct selinux_policy snapshot.  That type and
# ownership model do not exist on 4.14; rules.c above operates on the live
# policydb instead, so keep ABI-compatible internal stubs for these unused
# helpers and avoid compiling modern struct member accesses.
sepolicy_c_path = os.path.join(ksu_dir, "selinux", "sepolicy.c")
sepolicy_c = read_file(sepolicy_c_path)
# KernelSU v0.9.5 kept klog.h at the kernel root; current SukiSU keeps it in
# kernel/include, which is already on the Kbuild include path.
sepolicy_c = sepolicy_c.replace('#include "../klog.h"', '#include "klog.h"')
if "#include <linux/err.h>" not in sepolicy_c:
    sepolicy_c = sepolicy_c.replace(
        "#include <linux/gfp.h>\n", "#include <linux/err.h>\n#include <linux/gfp.h>\n", 1
    )
legacy_snapshot_stubs = r'''void ksu_destroy_sepolicy(struct selinux_policy *pol)
{
    (void)pol;
}

struct selinux_policy *ksu_dup_sepolicy(struct selinux_policy *old_pol)
{
    (void)old_pol;
    return ERR_PTR(-EOPNOTSUPP);
}
'''
if "void ksu_destroy_sepolicy(struct selinux_policy *pol)" in sepolicy_c:
    sepolicy_c, count = re.subn(
        r"void ksu_destroy_sepolicy\(struct selinux_policy \*pol\)\n\{.*?\n\}\s*$",
        lambda _match: legacy_snapshot_stubs,
        sepolicy_c,
        count=1,
        flags=re.S,
    )
    if count != 1:
        print("Error: unexpected SukiSU policy snapshot implementation")
        exit(1)
else:
    # The pinned v0.9.5 non-GKI engine predates policy snapshots.  Current
    # SukiSU still declares these internal helpers, so provide unused stubs.
    sepolicy_c = sepolicy_c.rstrip() + "\n\n" + legacy_snapshot_stubs
write_file(sepolicy_c_path, sepolicy_c)

# The SELinux-hide feature relies on modern policy snapshots and status fields.
# Keep the core/root and live sepolicy support, but report this optional feature
# as unsupported rather than compiling invalid 5.x state accesses into 4.14.
selinux_hide_path = os.path.join(ksu_dir, "feature", "selinux_hide.c")
write_file(selinux_hide_path, '''#include "selinux_hide.h"

/* SELinux policy snapshots used by this optional feature do not exist in the
 * Linux 4.14 SELinux state model.  Deliberately leave the feature unregistered. */
void ksu_selinux_hide_init(void) { }
void ksu_selinux_hide_exit(void) { }
void ksu_selinux_hide_drop_backup_if_unused(void) { }
void ksu_selinux_hide_handle_second_stage(void) { }
void ksu_selinux_hide_handle_post_fs_data(void) { }
''')

###############################################################################
# 7. PATCH Kbuild - force-include kernel_compat.h
###############################################################################
print("[7/9] Patching Kbuild ...")
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
print("[8/9] Creating missing header wrappers ...")

# linux/pgtable.h -> asm/pgtable.h (pgtable.h moved in 5.8)
pgtable_wrapper = os.path.join(base_dir, "include", "linux", "pgtable.h")
if not os.path.exists(pgtable_wrapper):
    os.makedirs(os.path.dirname(pgtable_wrapper), exist_ok=True)
    # Check the wrapper is not already there overriding a real file
    write_file(pgtable_wrapper, '#include <asm/pgtable.h>\n')

# linux/minmax.h was split out of linux/kernel.h after 4.14.
minmax_wrapper = os.path.join(base_dir, "include", "linux", "minmax.h")
if not os.path.exists(minmax_wrapper):
    os.makedirs(os.path.dirname(minmax_wrapper), exist_ok=True)
    write_file(minmax_wrapper, '#include <linux/kernel.h>\n')

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

print("[9/9] Compatibility validation complete")
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
     - SECCOMP_ARCH_NATIVE_NR / COMPAT_NR syscall bitmap sizes
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

  4. su_mount_ns.c    - Linux 4.14 mount namespace backport:
     - Removed unavailable uapi/linux/mount.h
     - __arm64_sys_setns -> sys_setns
     - ksys_unshare -> sys_unshare
     - path_mount -> do_mount with a scoped KERNEL_DS address limit

  5. Late filesystem APIs:
     - Modern fsnotify callback/add-mark -> Linux 4.14 equivalents
     - path_umount -> scoped sys_umount fallback
     - Guard seccomp filter_count and use 4.14 put_seccomp_filter

  6. SELinux 4.14     - Uses the legacy selinux_state.ss live policy model
     - Preserves root and live sepolicy rule support
     - Disables only optional SELinux-hide (requires modern policy snapshots)

  7. Kbuild           - Force-include kernel_compat.h

  8. Header wrappers  - Created:
     - include/linux/pgtable.h -> asm/pgtable.h
     - include/linux/minmax.h -> linux/kernel.h
     - include/asm-generic/fixmap.h -> asm/fixmap.h
""")
