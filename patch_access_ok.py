import os

# Check both paths to make it work regardless of current working directory
target_dir = os.path.join("drivers", "kernelsu")
if not os.path.exists(target_dir):
    target_dir = os.path.join("kernel-source", "drivers", "kernelsu")

if not os.path.exists(target_dir):
    print(f"Error: drivers/kernelsu directory not found! (Tried: drivers/kernelsu and kernel-source/drivers/kernelsu)")
    exit(1)

print(f"Found SukiSU driver directory at: {target_dir}")

# We define a unique compat macro that doesn't conflict or recurse
patch_code = """
#include <linux/version.h>
#if LINUX_VERSION_CODE < KERNEL_VERSION(5, 0, 0)
#ifndef VERIFY_READ
#define VERIFY_READ 0
#endif
#define ksu_access_ok(addr, size) access_ok(VERIFY_READ, (addr), (size))
#else
#define ksu_access_ok(addr, size) access_ok((addr), (size))
#endif
"""

patched_count = 0

for root, dirs, files in os.walk(target_dir):
    for file in files:
        if file.endswith((".c", ".h")):
            filepath = os.path.join(root, file)
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            # Check if access_ok is used in this file
            if "access_ok(" in content:
                print(f"Patching access_ok in {filepath}")
                
                # Replace access_ok with ksu_access_ok
                content = content.replace("access_ok(", "ksu_access_ok(")
                
                # Find the last #include in the file, and insert our patch after it
                lines = content.splitlines()
                insert_idx = -1
                for idx, line in enumerate(lines):
                    if line.strip().startswith("#include"):
                        insert_idx = idx
                
                if insert_idx != -1:
                    lines.insert(insert_idx + 1, patch_code)
                    new_content = "\n".join(lines)
                else:
                    new_content = patch_code + "\n" + content
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                patched_count += 1

print(f"Successfully patched {patched_count} files.")
