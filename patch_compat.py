import os

# Check both paths to make it work regardless of current working directory
base_dir = "kernel-source"
if not os.path.exists(base_dir):
    base_dir = "."

ksu_dir = os.path.join(base_dir, "drivers", "kernelsu")

if not os.path.exists(ksu_dir):
    print("Error: drivers/kernelsu directory not found!")
    exit(1)

# 1. Update kernel_compat.h
compat_path = os.path.join(ksu_dir, "kernel_compat.h")
with open(compat_path, "r", encoding="utf-8") as f:
    compat_content = f.read()

# Fix SukiSU-Ultra header guard collision:
# both kernel_compat.h and infra/seccomp_cache.h use __KSU_H_KERNEL_COMPAT,
# which causes seccomp_cache.h to be skipped when kernel_compat.h is force-included.
compat_content = compat_content.replace("__KSU_H_KERNEL_COMPAT", "__KSU_H_KERNEL_COMPAT_H_COMPAT")

# Add standard headers at the top of kernel_compat.h to resolve implicit declaration errors
required_headers = [
    "#include <linux/uaccess.h>",
    "#include <linux/syscalls.h>",
    "#include <asm/pgtable.h>"
]

header_injection = ""
for header in required_headers:
    if header not in compat_content:
        header_injection += header + "\n"

if header_injection:
    if "#define __KSU_H_KERNEL_COMPAT_H_COMPAT" in compat_content:
        compat_content = compat_content.replace(
            "#define __KSU_H_KERNEL_COMPAT_H_COMPAT",
            "#define __KSU_H_KERNEL_COMPAT_H_COMPAT\n" + header_injection.strip()
        )
    else:
        compat_content = header_injection + compat_content

compat_addition = """
/* Compatibility layer for Linux < 4.19 (Android 4.14 kernel compatibility) */
#ifndef MODULE_IMPORT_NS
#define MODULE_IMPORT_NS(ns)
#endif

#if defined(__aarch64__) && LINUX_VERSION_CODE < KERNEL_VERSION(4, 19, 0)
#ifndef _KSU_SYSCALL_FN_T
#define _KSU_SYSCALL_FN_T
struct pt_regs;
typedef long (*syscall_fn_t)(const struct pt_regs *regs);
#endif
#endif

/* Compatibility for ksys_* functions introduced in Linux 4.17 */
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
#endif

/* Compatibility for __flush_icache_range in Linux < 4.19 */
#if LINUX_VERSION_CODE < KERNEL_VERSION(4, 19, 0)
#ifndef __flush_icache_range
#define __flush_icache_range flush_icache_range
#endif
#endif

/* Compatibility for copy_from_user_nofault in Linux < 5.8 */
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
#ifndef _KSU_COPY_TO_KERNEL_NOFAULT
#define _KSU_COPY_TO_KERNEL_NOFAULT
static inline long copy_to_kernel_nofault(void *dst, const void *src, size_t size)
{
    return probe_kernel_write(dst, src, size);
}
#endif
#endif
"""

# Insert compat_addition at the top of the file (right after <linux/version.h>) to ensure it is defined before usage
if "#include <linux/version.h>" in compat_content:
    new_compat = compat_content.replace(
        "#include <linux/version.h>",
        "#include <linux/version.h>\n" + compat_addition
    )
else:
    # Fallback to inserting after the header definition
    new_compat = compat_content.replace(
        "#define __KSU_H_KERNEL_COMPAT_H_COMPAT",
        "#define __KSU_H_KERNEL_COMPAT_H_COMPAT\n" + compat_addition
    )

with open(compat_path, "w", encoding="utf-8") as f:
    f.write(new_compat)
print("Updated kernel_compat.h with top-level compatibility layer")

# 2. Update Kbuild to force-include kernel_compat.h in all compilations
kbuild_path = os.path.join(ksu_dir, "Kbuild")
with open(kbuild_path, "r", encoding="utf-8") as f:
    kbuild_content = f.read()

force_include_flag = "\nccflags-y += -include $(KSU_KERNEL_DIR)/kernel_compat.h\n"
if force_include_flag.strip() not in kbuild_content:
    new_kbuild = kbuild_content + force_include_flag
    with open(kbuild_path, "w", encoding="utf-8") as f:
        f.write(new_kbuild)
    print("Updated Kbuild with force-include flag")
else:
    print("Kbuild already updated")
