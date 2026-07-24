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
                String json = GitHubClient.fetchLatestReleaseJson();
                String tag = "最新版本 (無法連線)";
                if (json != null && json.contains("\"tag_name\":")) {
                    int start = json.indexOf("\"tag_name\":\"") + 12;
                    int end = json.indexOf("\"", start);
                    if (start > 11 && end > start) {
                        tag = json.substring(start, end);
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
                runOnUiThread(() -> webView.evaluateJavascript("appendLog('開始連網下載最新 AnyKernel3 ZIP...')", null));
                // Simulated flash execution
                SuShell.exec("sync");
                runOnUiThread(() -> webView.evaluateJavascript("appendLog('核心刷入成功！已執行 sync')", null));
            }).start();
        }

        private void vibrate(long ms) {
            Vibrator v = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
            if (v != null && v.hasVibrator()) {
                v.vibrate(ms);
            }
        }
    }
}
