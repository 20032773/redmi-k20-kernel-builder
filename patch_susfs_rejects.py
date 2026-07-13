import os

def patch_cmdline():
    filepath = "kernel-source/fs/proc/cmdline.c"
    if not os.path.exists(filepath):
        print(f"[!] {filepath} not found.")
        return False
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    if "CONFIG_KSU_SUSFS_SPOOF_CMDLINE_OR_BOOTCONFIG" in content:
        print("[*] cmdline.c already patched.")
        return True
        
    # 1. Add header declaration before cmdline_proc_show
    target_decl = "static int cmdline_proc_show"
    decl_patch = """#ifdef CONFIG_KSU_SUSFS_SPOOF_CMDLINE_OR_BOOTCONFIG
extern int susfs_spoof_cmdline_or_bootconfig(struct seq_file *m);
#endif

static int cmdline_proc_show"""
    
    if target_decl in content:
        content = content.replace(target_decl, decl_patch, 1)
    else:
        print("[!] Cannot find target declaration in cmdline.c")
        return False
        
    # 2. Add hook inside cmdline_proc_show
    target_body = "seq_printf(m, \"%s\\n\", saved_command_line);"
    body_patch = """#ifdef CONFIG_KSU_SUSFS_SPOOF_CMDLINE_OR_BOOTCONFIG
	if (!susfs_spoof_cmdline_or_bootconfig(m)) {
		seq_putc(m, '\\n');
		return 0;
	}
#endif
	seq_printf(m, "%s\\n", saved_command_line);"""
    
    if target_body in content:
        content = content.replace(target_body, body_patch, 1)
    else:
        print("[!] Cannot find target body in cmdline.c")
        return False
        
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("[+] Successfully patched cmdline.c")
    return True

def patch_task_mmu():
    filepath = "kernel-source/fs/proc/task_mmu.c"
    if not os.path.exists(filepath):
        print(f"[!] {filepath} not found.")
        return False
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    if "CONFIG_KSU_SUSFS_SUS_KSTAT" in content:
        print("[*] task_mmu.c already patched.")
        return True
        
    # 1. Add include
    target_inc = "#include <linux/shmem_fs.h>"
    inc_patch = """#include <linux/shmem_fs.h>
#ifdef CONFIG_KSU_SUSFS_SUS_KSTAT
#include <linux/susfs_def.h>
#endif"""
    if target_inc in content:
        content = content.replace(target_inc, inc_patch, 1)
    else:
        # Try alternate header
        target_inc = "#include <linux/uaccess.h>"
        inc_patch = """#include <linux/uaccess.h>
#ifdef CONFIG_KSU_SUSFS_SUS_KSTAT
#include <linux/susfs_def.h>
#endif"""
        if target_inc in content:
            content = content.replace(target_inc, inc_patch, 1)
        else:
            print("[!] Cannot find include target in task_mmu.c")
            return False
            
    # 2. Add extern declaration before show_map_vma
    target_show_map = "static void\nshow_map_vma(struct seq_file *m, struct vm_area_struct *vma, int is_pid)"
    # Try alternate formatting
    if target_show_map not in content:
        target_show_map = "static void show_map_vma(struct seq_file *m, struct vm_area_struct *vma, int is_pid)"
        
    decl_patch = """#ifdef CONFIG_KSU_SUSFS_SUS_KSTAT
extern void susfs_sus_ino_for_show_map_vma(unsigned long ino, dev_t *out_dev, unsigned long *out_ino);
#endif

""" + target_show_map

    if target_show_map in content:
        content = content.replace(target_show_map, decl_patch, 1)
    else:
        print("[!] Cannot find show_map_vma signature in task_mmu.c")
        return False
        
    # 3. Add hook inside show_map_vma (target VMA file inode parsing)
    target_vma_file = """\tdev = inode->i_sb->s_dev;
		ino = inode->i_ino;"""
    # Let's search with regex or standard block replacement
    target_block = """\tif (file) {
		struct inode *inode = file_inode(vma->vm_file);
		dev = inode->i_sb->s_dev;
		ino = inode->i_ino;
		pgoff = ((loff_t)vma->vm_pgoff) << PAGE_SHIFT;
	}"""
    
    body_patch = """\tif (file) {
		struct inode *inode = file_inode(vma->vm_file);
#ifdef CONFIG_KSU_SUSFS_SUS_KSTAT
		if (unlikely(inode->i_state & INODE_STATE_SUS_KSTAT)) {
			susfs_sus_ino_for_show_map_vma(inode->i_ino, &dev, &ino);
			goto bypass_orig_flow;
		}
#endif
		dev = inode->i_sb->s_dev;
		ino = inode->i_ino;
#ifdef CONFIG_KSU_SUSFS_SUS_KSTAT
bypass_orig_flow:
#endif
		pgoff = ((loff_t)vma->vm_pgoff) << PAGE_SHIFT;
	}"""
    
    if target_block in content:
        content = content.replace(target_block, body_patch, 1)
    else:
        # Try variation with different indentation or spacing
        target_block_alt = """\tif (file) {
		struct inode *inode = file_inode(vma->vm_file);
		dev = inode->i_sb->s_dev;
		ino = inode->i_ino;
		pgoff = ((loff_t)vma->vm_pgoff) << PAGE_SHIFT;
	}"""
        # We can search dynamically or replace just the inode part
        target_inode = """\t\tdev = inode->i_sb->s_dev;
\t\tino = inode->i_ino;"""
        inode_patch = """#ifdef CONFIG_KSU_SUSFS_SUS_KSTAT
\t\tif (unlikely(inode->i_state & INODE_STATE_SUS_KSTAT)) {
\t\t\tsusfs_sus_ino_for_show_map_vma(inode->i_ino, &dev, &ino);
\t\t\tgoto bypass_orig_flow;
\t\t}
#endif
\t\tdev = inode->i_sb->s_dev;
\t\tino = inode->i_ino;
#ifdef CONFIG_KSU_SUSFS_SUS_KSTAT
bypass_orig_flow:
#endif"""
        if target_inode in content:
            content = content.replace(target_inode, inode_patch, 1)
        else:
            print("[!] Cannot find target block in show_map_vma inside task_mmu.c")
            return False
            
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("[+] Successfully patched task_mmu.c")
    return True

if __name__ == "__main__":
    s1 = patch_cmdline()
    s2 = patch_task_mmu()
    if not (s1 and s2):
        print("[!] Patching failed.")
        exit(1)
    else:
        print("[*] All custom patches applied successfully.")
