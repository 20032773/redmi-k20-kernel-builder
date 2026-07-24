package com.k0983.k20updater.core;

import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.InputStreamReader;

public class SuShell {
    public static boolean checkRoot() {
        Process p = null;
        BufferedReader reader = null;
        try {
            p = Runtime.getRuntime().exec("su -c id");
            reader = new BufferedReader(new InputStreamReader(p.getInputStream()));
            String line = reader.readLine();
            p.waitFor();
            return line != null && line.contains("uid=0");
        } catch (Exception e) {
            return false;
        } finally {
            if (reader != null) {
                try {
                    reader.close();
                } catch (Exception ignored) {
                }
            }
            if (p != null) {
                p.destroy();
            }
        }
    }

    public static String exec(String cmd) {
        StringBuilder sb = new StringBuilder();
        Process p = null;
        DataOutputStream os = null;
        BufferedReader reader = null;
        try {
            p = Runtime.getRuntime().exec("su");
            os = new DataOutputStream(p.getOutputStream());
            os.writeBytes(cmd + "\nexit\n");
            os.flush();

            reader = new BufferedReader(new InputStreamReader(p.getInputStream()));
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line).append("\n");
            }
            p.waitFor();
        } catch (Exception e) {
            sb.append("Error: ").append(e.getMessage());
        } finally {
            if (os != null) {
                try {
                    os.close();
                } catch (Exception ignored) {
                }
            }
            if (reader != null) {
                try {
                    reader.close();
                } catch (Exception ignored) {
                }
            }
            if (p != null) {
                p.destroy();
            }
        }
        return sb.toString().trim();
    }
}
