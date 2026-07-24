package com.k0983.k20updater;

import android.app.Activity;
import android.content.Context;
import android.os.Bundle;
import android.os.Vibrator;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;
import com.k0983.k20updater.core.GitHubClient;
import com.k0983.k20updater.core.SuShell;
import com.k0983.k20updater.data.AddonDManager;
import org.json.JSONArray;
import org.json.JSONObject;

public class MainActivity extends Activity {
    private WebView webView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        webView = new WebView(this);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        webView.addJavascriptInterface(new WebAppInterface(this), "Android");
        webView.loadUrl("file:///android_asset/index.html");
        setContentView(webView);
    }

    public class WebAppInterface {
        Context mContext;

        WebAppInterface(Context c) {
            mContext = c;
        }

        @JavascriptInterface
        public String getKernelVersion() {
            return SuShell.exec("uname -r");
        }

        @JavascriptInterface
        public boolean checkRoot() {
            return SuShell.checkRoot();
        }

        @JavascriptInterface
        public boolean isAddonDInstalled() {
            return AddonDManager.isAddonDInstalled();
        }

        @JavascriptInterface
        public void setAddonD(boolean enable) {
            if (enable) {
                AddonDManager.enableAddonD("/data/adb/k20_kernel_backup.zip");
            } else {
                AddonDManager.disableAddonD();
            }
            vibrate(50);
        }

        @JavascriptInterface
        public void fetchLatestRelease() {
            new Thread(() -> {
                String jsonStr = GitHubClient.fetchLatestReleaseJson();
                String tag = "最新版本 (無法連線)";
                if (jsonStr != null && !jsonStr.trim().isEmpty()) {
                    try {
                        JSONObject json = new JSONObject(jsonStr);
                        tag = json.optString("tag_name", "最新版本 (無法連線)");
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                }
                final String finalTag = tag;
                runOnUiThread(() -> webView.evaluateJavascript("updateReleaseInfo('" + finalTag + "')", null));
            }).start();
        }

        @JavascriptInterface
        public void startFlashProcess() {
            vibrate(80);
            new Thread(() -> {
                logToWeb("開始連網下載最新 AnyKernel3 ZIP...");
                String downloadUrl = null;
                String jsonStr = GitHubClient.fetchLatestReleaseJson();
                if (jsonStr != null && !jsonStr.trim().isEmpty()) {
                    try {
                        JSONObject json = new JSONObject(jsonStr);
                        JSONArray assets = json.optJSONArray("assets");
                        if (assets != null) {
                            for (int i = 0; i < assets.length(); i++) {
                                JSONObject asset = assets.getJSONObject(i);
                                String name = asset.optString("name", "");
                                String url = asset.optString("browser_download_url", "");
                                if (name.endsWith(".zip") || url.endsWith(".zip")) {
                                    downloadUrl = url;
                                    break;
                                }
                            }
                        }
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                }

                if (downloadUrl == null || downloadUrl.isEmpty()) {
                    downloadUrl = "https://github.com/20032773/redmi-k20-kernel-builder/releases/latest/download/AnyKernel3-k20.zip";
                }

                logToWeb("下載目標: /data/local/tmp/k20_kernel.zip");
                String downloadCmd = "curl -sSL \"" + downloadUrl + "\" -o /data/local/tmp/k20_kernel.zip || wget -O /data/local/tmp/k20_kernel.zip \"" + downloadUrl + "\"";
                SuShell.exec(downloadCmd);

                logToWeb("備份核心 ZIP 至 /data/adb/k20_kernel_backup.zip...");
                SuShell.exec("cp /data/local/tmp/k20_kernel.zip /data/adb/k20_kernel_backup.zip");

                logToWeb("解壓縮與執行 AnyKernel3 刷入腳本...");
                String flashCmd = "rm -rf /data/local/tmp/anykernel && " +
                        "mkdir -p /data/local/tmp/anykernel && " +
                        "unzip -o /data/local/tmp/k20_kernel.zip -d /data/local/tmp/anykernel && " +
                        "cd /data/local/tmp/anykernel && " +
                        "if [ -f anykernel.sh ]; then sh anykernel.sh; elif [ -f flash.sh ]; then sh flash.sh; else sh META-INF/com/google/android/update-binary 1 2 /data/local/tmp/k20_kernel.zip; fi && " +
                        "sync";
                String flashResult = SuShell.exec(flashCmd);
                if (flashResult != null && !flashResult.trim().isEmpty()) {
                    logToWeb("刷入日誌: " + flashResult);
                }

                logToWeb("核心刷入成功！已執行 sync");
                vibrate(150);
            }).start();
        }

        private void logToWeb(String msg) {
            final String safeMsg = msg.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "");
            runOnUiThread(() -> webView.evaluateJavascript("appendLog('" + safeMsg + "')", null));
        }

        private void vibrate(long ms) {
            Vibrator v = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
            if (v != null && v.hasVibrator()) {
                v.vibrate(ms);
            }
        }
    }
}
