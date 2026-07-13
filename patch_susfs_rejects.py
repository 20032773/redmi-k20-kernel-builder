import os

def get_filepath(rel_path):
    # Try local path first (if running inside kernel-source directory)
    if os.path.exists(rel_path):
        return rel_path
    # Try parent directory prefix (if running from repository root)
    alt_path = os.path.join("kernel-source", rel_path)
    if os.path.exists(alt_path):
        return alt_path
    return None

def patch_cmdline():
    filepath = get_filepath("fs/proc/cmdline.c")
    if not filepath:
        print("[!] fs/proc/cmdline.c not found.")
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
    print(f"[+] Successfully patched {filepath}")
    return True

def patch_task_mmu():
    filepath = get_filepath("fs/proc/task_mmu.c")
    if not filepath:
        print("[!] fs/proc/task_mmu.c not found.")
        return False
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Check and patch include if missing (since Hunk 1 fails)
    if "linux/susfs_def.h" not in content:
        target_inc = "#include <linux/shmem_fs.h>"
        inc_patch = """#include <linux/shmem_fs.h>
#ifdef CONFIG_KSU_SUSFS_SUS_KSTAT
#include <linux/susfs_def.h>
#endif"""
        if target_inc in content:
            content = content.replace(target_inc, inc_patch, 1)
        else:
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
        print("[+] Added susfs_def.h include to task_mmu.c")
            
    # Check and patch hooks if missing
    if "susfs_sus_ino_for_show_map_vma" not in content:
        target_show_map = "static void\nshow_map_vma(struct seq_file *m, struct vm_area_struct *vma, int is_pid)"
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
            
        target_inode = """		dev = inode->i_sb->s_dev;
		ino = inode->i_ino;"""
        inode_patch = """#ifdef CONFIG_KSU_SUSFS_SUS_KSTAT
		if (unlikely(inode->i_state & INODE_STATE_SUS_KSTAT)) {
			susfs_sus_ino_for_show_map_vma(inode->i_ino, &dev, &ino);
			goto bypass_orig_flow;
		}
#endif
		dev = inode->i_sb->s_dev;
		ino = inode->i_ino;
#ifdef CONFIG_KSU_SUSFS_SUS_KSTAT
bypass_orig_flow:
#endif"""
        if target_inode in content:
            content = content.replace(target_inode, inode_patch, 1)
        else:
            target_inode_alt = """\t\tdev = inode->i_sb->s_dev;
\t\tino = inode->i_ino;"""
            inode_patch_alt = """#ifdef CONFIG_KSU_SUSFS_SUS_KSTAT
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
            if target_inode_alt in content:
                content = content.replace(target_inode_alt, inode_patch_alt, 1)
            else:
                print("[!] Cannot find target block in show_map_vma inside task_mmu.c")
                return False
        print("[+] Added hooks to task_mmu.c")
            
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[+] Successfully patched {filepath}")
    return True

def patch_namespace():
    filepath = get_filepath("fs/namespace.c")
    if not filepath:
        print("[!] fs/namespace.c not found.")
        return False
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    # 1. Add forward declarations at the top before mp_hash to fix compiler error
    if "static inline bool may_mount(void);" not in content:
        target = "static inline struct hlist_head *mp_hash"
        declarations = """static inline bool may_mount(void);
static inline int check_mnt(struct mount *mnt);
static int do_umount(struct mount *mnt, int flags);
static void mntput_no_expire(struct mount *mnt);

static inline struct hlist_head *mp_hash"""

        if target in content:
            content = content.replace(target, declarations, 1)
            print("[+] Added forward declarations to fs/namespace.c")
        else:
            print("[!] Cannot find mp_hash declaration in fs/namespace.c")
            return False
            
    # 2. Patch failed Hunk #2 (susfs_mnt_alloc_id) if missing
    if "susfs_mnt_alloc_id" not in content:
        target_alloc_id = "static int mnt_alloc_id(struct mount *mnt)"
        alloc_id_patch = """#ifdef CONFIG_KSU_SUSFS_SUS_MOUNT
static int susfs_mnt_alloc_id(struct mount *mnt)
{
	int res;

retry:
	ida_pre_get(&susfs_mnt_id_ida, GFP_KERNEL);
	spin_lock(&mnt_id_lock);
	res = ida_get_new_above(&susfs_mnt_id_ida, susfs_mnt_id_start, &mnt->mnt_id);
	if (!res)
		susfs_mnt_id_start = mnt->mnt_id + 1;
	spin_unlock(&mnt_id_lock);
	if (res == -EAGAIN)
		goto retry;

	return res;
}
#endif

static int mnt_alloc_id(struct mount *mnt)"""
        
        if target_alloc_id in content:
            content = content.replace(target_alloc_id, alloc_id_patch, 1)
            print("[+] Successfully patched susfs_mnt_alloc_id into fs/namespace.c")
        else:
            print("[!] Cannot find mnt_alloc_id signature in fs/namespace.c")
            return False
            
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[+] Successfully patched {filepath}")
    return True

if __name__ == "__main__":
    s1 = patch_cmdline()
    s2 = patch_task_mmu()
    s3 = patch_namespace()
    if not (s1 and s2 and s3):
        print("[!] Patching failed.")
        exit(1)
    else:
        print("[*] All custom patches applied successfully.")
