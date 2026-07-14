import os

kernel_source = "kernel-source"
target_dir = os.path.join(kernel_source, "drivers", "kernelsu")

if not os.path.exists(target_dir):
    print("Error: drivers/kernelsu directory not found!")
    exit(1)

patch_code = """
#include <linux/version.h>
#if LINUX_VERSION_CODE < KERNEL_VERSION(5, 0, 0)
#ifdef access_ok
#undef access_ok
#define access_ok(addr, size) access_ok(VERIFY_READ, (addr), (size))
#endif
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
                
                # We find the last #include in the file, and insert our patch after it
                lines = content.splitlines()
                insert_idx = -1
                for idx, line in enumerate(lines):
                    if line.strip().startswith("#include"):
                        insert_idx = idx
                
                if insert_idx != -1:
                    lines.insert(insert_idx + 1, patch_code)
                    new_content = "\n".join(lines)
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    patched_count += 1
                else:
                    # Fallback to appending at the top
                    new_content = patch_code + "\n" + content
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    patched_count += 1

print(f"Successfully patched {patched_count} files.")
