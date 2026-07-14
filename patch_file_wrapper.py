#!/usr/bin/env python3
"""Backport SukiSU Ultra's file wrapper to vendor kernels with old VFS APIs.

The current SukiSU file wrapper mirrors every modern ``file_operations``
member.  Android 4.14 vendor kernels do not provide several of those members,
and they also predate ``alloc_file_pseudo()``.  This patch keeps each optional
operation only when the target kernel actually exposes it and supplies the
4.14 ``alloc_file()`` equivalent.

The substitutions are deliberately strict: an upstream refactor must fail the
workflow here instead of silently producing a partially patched kernel.
"""

from pathlib import Path
import sys


ROOT = Path("kernel-source")
if not ROOT.exists():
    ROOT = Path(".")

SOURCE = ROOT / "drivers" / "kernelsu" / "infra" / "file_wrapper.c"
KBUILD = ROOT / "drivers" / "kernelsu" / "Kbuild"


def replace_once(text: str, old: str, new: str, description: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"{description}: expected exactly one upstream match, found {count}"
        )
    return text.replace(old, new, 1)


def main() -> int:
    if not SOURCE.is_file() or not KBUILD.is_file():
        print("error: SukiSU Ultra was not found under drivers/kernelsu", file=sys.stderr)
        return 1

    source = SOURCE.read_text(encoding="utf-8")
    if "KSU_COMPAT_HAS_FOP_IOPOLL" in source:
        print("[*] file_wrapper.c is already patched")
        return 0

    iopoll = """#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 1, 0)
static int ksu_wrapper_iopoll(struct kiocb *kiocb, struct io_comp_batch *icb, unsigned int v)
{
    struct ksu_file_wrapper *data = kiocb->ki_filp->private_data;
    struct file *orig = data->orig;
    kiocb->ki_filp = orig;
    return orig->f_op->iopoll(kiocb, icb, v);
}
#else
static int ksu_wrapper_iopoll(struct kiocb *kiocb, bool spin)
{
    struct ksu_file_wrapper *data = kiocb->ki_filp->private_data;
    struct file *orig = data->orig;
    kiocb->ki_filp = orig;
    return orig->f_op->iopoll(kiocb, spin);
}
#endif
"""
    source = replace_once(
        source,
        iopoll,
        "#ifdef KSU_COMPAT_HAS_FOP_IOPOLL\n" + iopoll + "#endif\n",
        "guard iopoll implementation",
    )

    remap = """static loff_t ksu_wrapper_remap_file_range(struct file *file_in, loff_t pos_in, struct file *file_out, loff_t pos_out,
                                           loff_t len, unsigned int remap_flags)
{
    if (remap_flags & REMAP_FILE_DEDUP) {
        struct ksu_file_wrapper *data = file_out->private_data;
        struct file *orig = data->orig;
        return orig->f_op->remap_file_range(file_in, pos_in, orig, pos_out, len, remap_flags);
    } else {
        struct ksu_file_wrapper *data = file_in->private_data;
        struct file *orig = data->orig;
        return orig->f_op->remap_file_range(orig, pos_in, file_out, pos_out, len, remap_flags);
    }
}
"""
    source = replace_once(
        source,
        remap,
        "#ifdef KSU_COMPAT_HAS_FOP_REMAP_FILE_RANGE\n" + remap + "#endif\n",
        "guard remap_file_range implementation",
    )

    fadvise = """static int ksu_wrapper_fadvise(struct file *fp, loff_t off1, loff_t off2, int flags)
{
    struct ksu_file_wrapper *data = fp->private_data;
    struct file *orig = data->orig;
    if (orig->f_op->fadvise) {
        return orig->f_op->fadvise(orig, off1, off2, flags);
    }
    return -EINVAL;
}
"""
    source = replace_once(
        source,
        fadvise,
        "#ifdef KSU_COMPAT_HAS_FOP_FADVISE\n" + fadvise + "#endif\n",
        "guard fadvise implementation",
    )

    source = replace_once(
        source,
        "    p->ops.iopoll = fp->f_op->iopoll ? ksu_wrapper_iopoll : NULL;",
        """#ifdef KSU_COMPAT_HAS_FOP_IOPOLL
    p->ops.iopoll = fp->f_op->iopoll ? ksu_wrapper_iopoll : NULL;
#endif""",
        "guard iopoll assignment",
    )
    source = replace_once(
        source,
        """#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 12, 0)
    p->ops.fop_flags = fp->f_op->fop_flags;
#else
    p->ops.mmap_supported_flags = fp->f_op->mmap_supported_flags;
#endif""",
        """#ifdef KSU_COMPAT_HAS_FOP_MMAP_SUPPORTED_FLAGS
#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 12, 0)
    p->ops.fop_flags = fp->f_op->fop_flags;
#else
    p->ops.mmap_supported_flags = fp->f_op->mmap_supported_flags;
#endif
#endif""",
        "guard mmap/fop flags assignment",
    )
    source = replace_once(
        source,
        "    p->ops.remap_file_range = fp->f_op->remap_file_range ? ksu_wrapper_remap_file_range : NULL;",
        """#ifdef KSU_COMPAT_HAS_FOP_REMAP_FILE_RANGE
    p->ops.remap_file_range = fp->f_op->remap_file_range ? ksu_wrapper_remap_file_range : NULL;
#endif""",
        "guard remap_file_range assignment",
    )
    source = replace_once(
        source,
        "    p->ops.fadvise = fp->f_op->fadvise ? ksu_wrapper_fadvise : NULL;",
        """#ifdef KSU_COMPAT_HAS_FOP_FADVISE
    p->ops.fadvise = fp->f_op->fadvise ? ksu_wrapper_fadvise : NULL;
#endif""",
        "guard fadvise assignment",
    )

    alloc_call = """    file = alloc_file_pseudo(inode, anon_inode_mnt, name, flags & (O_ACCMODE | O_NONBLOCK), fops);
    if (IS_ERR(file))
        goto err_iput;
"""
    alloc_compat = """#ifdef KSU_COMPAT_HAS_ALLOC_FILE_PSEUDO
    file = alloc_file_pseudo(inode, anon_inode_mnt, name, flags & (O_ACCMODE | O_NONBLOCK), fops);
    if (IS_ERR(file))
        goto err_iput;
#else
    /* Linux 4.14 equivalent of alloc_file_pseudo().  The dentry owns the
     * inode reference after d_instantiate(), so alloc_file() failure must use
     * path_put() and skip the separate iput() path. */
    {
        const struct qstr qname = QSTR_INIT(name, strlen(name));
        struct path path;

        path.dentry = d_alloc_pseudo(anon_inode_mnt->mnt_sb, &qname);
        if (!path.dentry) {
            file = ERR_PTR(-ENOMEM);
            goto err_iput;
        }
        path.mnt = mntget(anon_inode_mnt);
        d_instantiate(path.dentry, inode);

        file = alloc_file(&path, OPEN_FMODE(flags), fops);
        if (IS_ERR(file)) {
            path_put(&path);
            goto err;
        }
        file->f_flags = flags & (O_ACCMODE | O_NONBLOCK);
    }
#endif
"""
    source = replace_once(
        source, alloc_call, alloc_compat, "backport alloc_file_pseudo"
    )

    SOURCE.write_text(source, encoding="utf-8")

    kbuild = KBUILD.read_text(encoding="utf-8")
    marker = "# BEGIN redmi-k20 old-VFS capability detection"
    if marker not in kbuild:
        kbuild += """

# BEGIN redmi-k20 old-VFS capability detection
# Vendor kernels routinely backport VFS members without changing VERSION_CODE,
# so test the actual headers instead of guessing from the kernel version.
ifeq ($(shell grep -q "iopoll" $(srctree)/include/linux/fs.h; echo $$?),0)
ccflags-y += -DKSU_COMPAT_HAS_FOP_IOPOLL
endif
ifeq ($(shell grep -q "mmap_supported_flags" $(srctree)/include/linux/fs.h; echo $$?),0)
ccflags-y += -DKSU_COMPAT_HAS_FOP_MMAP_SUPPORTED_FLAGS
endif
ifeq ($(shell grep -q "remap_file_range" $(srctree)/include/linux/fs.h; echo $$?),0)
ccflags-y += -DKSU_COMPAT_HAS_FOP_REMAP_FILE_RANGE
endif
ifeq ($(shell grep -q "fadvise" $(srctree)/include/linux/fs.h; echo $$?),0)
ccflags-y += -DKSU_COMPAT_HAS_FOP_FADVISE
endif
ifeq ($(shell grep -q "alloc_file_pseudo" $(srctree)/include/linux/file.h; echo $$?),0)
ccflags-y += -DKSU_COMPAT_HAS_ALLOC_FILE_PSEUDO
endif
# END redmi-k20 old-VFS capability detection
"""
        KBUILD.write_text(kbuild, encoding="utf-8")

    print("[+] Patched SukiSU file_wrapper for old vendor VFS APIs")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
