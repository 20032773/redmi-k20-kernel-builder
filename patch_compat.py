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

# Add #include <linux/uaccess.h> at the top to resolve implicit declaration errors
if "#include <linux/uaccess.h>" not in compat_content:
    if "#define __KSU_H_KERNEL_COMPAT" in compat_content:
        compat_content = compat_content.replace(
            "#define __KSU_H_KERNEL_COMPAT",
            "#define __KSU_H_KERNEL_COMPAT\n#include <linux/uaccess.h>"
        )
    else:
        compat_content = "#include <linux/uaccess.h>\n" + compat_content

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
"""

# Append before #endif at the end if it exists, otherwise append at the end
if "#endif" in compat_content:
    parts = compat_content.rsplit("#endif", 1)
    new_compat = parts[0] + compat_addition + "\n#endif" + parts[1]
else:
    new_compat = compat_content + "\n" + compat_addition

with open(compat_path, "w", encoding="utf-8") as f:
    f.write(new_compat)
print("Updated kernel_compat.h with uaccess.h and compat macros")

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
