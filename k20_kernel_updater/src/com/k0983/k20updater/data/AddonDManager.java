package com.k0983.k20updater.data;

import com.k0983.k20updater.core.SuShell;

public class AddonDManager {
    private static final String ADDOND_PATH = "/system/addon.d/99-k20-kernel.sh";

    public static boolean isAddonDInstalled() {
        String res = SuShell.exec("test -f " + ADDOND_PATH + " && echo 'exists'");
        return res.contains("exists");
    }

    public static boolean enableAddonD(String backupZipPath) {
        String script = "#!/sbin/sh\n" +
                ". /tmp/backuptool.functions\n\n" +
                "list_files() {\ncat <<EOF\nEOF\n}\n\n" +
                "case \"$1\" in\n" +
                "  backup)\n" +
                "    # Backup kernel zip\n" +
                "    ;;\n" +
                "  restore)\n" +
                "    # Re-flash kernel zip post-OTA\n" +
                "    if [ -f \"" + backupZipPath + "\" ]; then\n" +
                "      # Unpack and flash AnyKernel3\n" +
                "      sync;\n" +
                "    fi\n" +
                "    ;;\n" +
                "esac\n";
        String cmd = "mount -o remount,rw /system && " +
                "echo '" + script + "' > " + ADDOND_PATH + " && " +
                "chmod 755 " + ADDOND_PATH;
        String res = SuShell.exec(cmd);
        return isAddonDInstalled();
    }

    public static boolean disableAddonD() {
        String cmd = "mount -o remount,rw /system && rm -f " + ADDOND_PATH;
        SuShell.exec(cmd);
        return !isAddonDInstalled();
    }
}
