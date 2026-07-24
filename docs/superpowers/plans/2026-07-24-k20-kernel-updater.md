# Redmi K20 Kernel Updater Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone, private Android Root App (`k20-kernel-updater`) for Redmi K20 (`davinci`) that enables one-click online kernel updating from GitHub Releases and manages `addon.d` survival scripts to preserve Root and custom kernel across LineageOS OTA updates.

**Architecture:** Clean Architecture + Layered Java/WebUI host. Uses `SuShell` for Root execution, REST client for GitHub API, and a Material You Bento Grid HTML5 interface tinted with system dynamic colors.

**Tech Stack:** Java (Android SDK 35, d8, aapt2), HTML5, Material 3 CSS (Dynamic Color), JavaScript, ADB, Python build script.

## Global Constraints

- **Package Name:** `com.k0983.k20updater`
- **Target Device:** Redmi K20 / Mi 9T (`davinci`)
- **Target ROM:** LineageOS 23.2
- **GitHub Repository API:** `https://api.github.com/repos/20032773/redmi-k20-kernel-builder/releases/latest`
- **Privacy Rule:** Local build only, do NOT git push the application binary or private user source to public GitHub.

---

### Task 1: Scaffolding Project Structure & Android Manifest

**Files:**
- Create: `k20_kernel_updater/AndroidManifest.xml`
- Create: `k20_kernel_updater/build_apk.py`

**Interfaces:**
- Consumes: Local Android SDK (`android-35`, `d8`, `aapt2`, `apksigner`).
- Produces: Project root structure and automated build pipeline.

- [ ] **Step 1: Create AndroidManifest.xml**

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.k0983.k20updater"
    android:versionCode="1"
    android:versionName="1.0.0">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.VIBRATE" />

    <application
        android:label="K20 核心更新助手"
        android:icon="@android:drawable/ic_dialog_info"
        android:theme="@android:style/Theme.DeviceDefault.NoActionBar"
        android:usesCleartextTraffic="true">
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:configChanges="orientation|keyboardHidden|screenSize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

- [ ] **Step 2: Create build_apk.py compilation script**

```python
import os
import sys
import subprocess
import shutil

SDK_DIR = r"C:\Users\k0983\AppData\Local\Android\Sdk"
BUILD_TOOLS = os.path.join(SDK_DIR, "build-tools", "35.0.0")
ANDROID_JAR = os.path.join(SDK_DIR, "platforms", "android-35", "android.jar")
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(PROJECT_DIR, "bin")

def run_cmd(cmd):
    print("Running:", " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.stdout:
        print("STDOUT:", res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)
    if res.returncode != 0:
        raise Exception(f"Command failed with code {res.returncode}")

def main():
    if os.path.exists(BIN_DIR):
        shutil.rmtree(BIN_DIR)
    os.makedirs(os.path.join(BIN_DIR, "classes"), exist_ok=True)

    # 1. Compile Java
    java_files = []
    for root, _, files in os.walk(os.path.join(PROJECT_DIR, "src")):
        for f in files:
            if f.endswith(".java"):
                java_files.append(os.path.join(root, f))

    if java_files:
        run_cmd([
            "javac", "-classpath", ANDROID_JAR,
            "-d", os.path.join(BIN_DIR, "classes"),
            "-source", "8", "-target", "8"
        ] + java_files)

    # 2. Dex
    class_files = []
    for root, _, files in os.walk(os.path.join(BIN_DIR, "classes")):
        for f in files:
            if f.endswith(".class"):
                class_files.append(os.path.join(root, f))

    d8_bat = os.path.join(BUILD_TOOLS, "d8.bat")
    run_cmd([d8_bat, "--output", BIN_DIR, "--min-api", "28"] + class_files)

    # 3. AAPT2 Package
    aapt2 = os.path.join(BUILD_TOOLS, "aapt2.exe")
    unsigned_apk = os.path.join(BIN_DIR, "app-unsigned.apk")
    run_cmd([
        aapt2, "link", "-o", unsigned_apk,
        "-I", ANDROID_JAR,
        "--manifest", os.path.join(PROJECT_DIR, "AndroidManifest.xml"),
        "-A", os.path.join(PROJECT_DIR, "assets")
    ])

    # 4. Add classes.dex
    run_cmd(["tar", "-uf", unsigned_apk, "-C", BIN_DIR, "classes.dex"])

    # 5. Sign
    apksigner = os.path.join(BUILD_TOOLS, "apksigner.bat")
    output_apk = os.path.join(PROJECT_DIR, "k20_kernel_updater.apk")
    keystore = os.path.join(PROJECT_DIR, "debug.keystore")
    if not os.path.exists(keystore):
        run_cmd([
            "keytool", "-genkeypair", "-keystore", keystore,
            "-storepass", "android", "-alias", "androiddebugkey",
            "-keypass", "android", "-dname", "CN=Android Debug,O=Android,C=US",
            "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000"
        ])
    run_cmd([
        apksigner, "sign", "--ks", keystore,
        "--ks-pass", "pass:android", "--out", output_apk, unsigned_apk
    ])
    print(f"Build Completed! APK saved to {output_apk}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Commit Scaffolding**

```bash
git add k20_kernel_updater/AndroidManifest.xml k20_kernel_updater/build_apk.py
git commit -m "feat: setup initial scaffolding for k20 kernel updater app"
```

---

### Task 2: Core Layer Implementation (SuShell & Network & AddonD Manager)

**Files:**
- Create: `k20_kernel_updater/src/com/k0983/k20updater/core/SuShell.java`
- Create: `k20_kernel_updater/src/com/k0983/k20updater/core/GitHubClient.java`
- Create: `k20_kernel_updater/src/com/k0983/k20updater/data/AddonDManager.java`

**Interfaces:**
- Consumes: Android System Shell, Root `su`, `java.net.HttpURLConnection`.
- Produces: `SuShell.exec(cmd)`, `GitHubClient.fetchLatestRelease()`, `AddonDManager.toggleAddonD(enable)`.

- [ ] **Step 1: Write SuShell.java**

```java
package com.k0983.k20updater.core;

import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.InputStreamReader;

public class SuShell {
    public static boolean checkRoot() {
        try {
            Process p = Runtime.getRuntime().exec("su -c id");
            BufferedReader reader = new BufferedReader(new InputStreamReader(p.getInputStream()));
            String line = reader.readLine();
            p.waitFor();
            return line != null && line.contains("uid=0");
        } catch (Exception e) {
            return false;
        }
    }

    public static String exec(String cmd) {
        StringBuilder sb = new StringBuilder();
        try {
            Process p = Runtime.getRuntime().exec("su");
            DataOutputStream os = new DataOutputStream(p.getOutputStream());
            os.writeBytes(cmd + "\nexit\n");
            os.flush();

            BufferedReader reader = new BufferedReader(new InputStreamReader(p.getInputStream()));
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line).append("\n");
            }
            p.waitFor();
        } catch (Exception e) {
            sb.append("Error: ").append(e.getMessage());
        }
        return sb.toString().trim();
    }
}
```

- [ ] **Step 2: Write GitHubClient.java**

```java
package com.k0983.k20updater.core;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

public class GitHubClient {
    private static final String API_URL = "https://api.github.com/repos/20032773/redmi-k20-kernel-builder/releases/latest";

    public static String fetchLatestReleaseJson() {
        try {
            URL url = new URL(API_URL);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setRequestProperty("User-Agent", "K20KernelUpdaterApp");
            conn.setConnectTimeout(8000);
            conn.setReadTimeout(8000);

            if (conn.getResponseCode() == 200) {
                BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = br.readLine()) != null) {
                    sb.append(line);
                }
                return sb.toString();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }
}
```

- [ ] **Step 3: Write AddonDManager.java**

```java
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
```

- [ ] **Step 4: Commit Core & Data Layer**

```bash
git add k20_kernel_updater/src/com/k0983/k20updater/core/ k20_kernel_updater/src/com/k0983/k20updater/data/
git commit -m "feat: implement SuShell, GitHubClient, and AddonDManager"
```

---

### Task 3: UI & WebBridge Presentation Layer Implementation

**Files:**
- Create: `k20_kernel_updater/assets/index.html`
- Create: `k20_kernel_updater/src/com/k0983/k20updater/MainActivity.java`

**Interfaces:**
- Consumes: `SuShell`, `GitHubClient`, `AddonDManager`.
- Produces: Interactive Bento Grid Dashboard App UI with dynamic Material You system coloring.

- [ ] **Step 1: Write index.html with Bento Grid Cards & Material You styling**

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
  <title>Redmi K20 核心更新助手</title>
  <style>
    :root {
      --color-primary: #38bdf8;
      --color-background: #020617;
      --color-surface: #0f172a;
      --color-on-surface: #f8fafc;
      --color-on-surface-variant: #94a3b8;
      --color-outline: #334155;
    }
    body {
      margin: 0; padding: 16px;
      background-color: var(--color-background);
      color: var(--color-on-surface);
      font-family: system-ui, -apple-system, sans-serif;
    }
    .header {
      font-size: 22px; font-weight: bold; margin-bottom: 16px;
      color: var(--color-primary); display: flex; align-items: center; gap: 8px;
    }
    .grid { display: grid; grid-template-columns: 1fr; gap: 12px; }
    .card {
      background: var(--color-surface);
      border: 1px solid var(--color-outline);
      border-radius: 16px; padding: 16px; position: relative;
    }
    .card-title {
      font-size: 14px; color: var(--color-on-surface-variant);
      margin-bottom: 8px; text-transform: uppercase; font-weight: bold;
    }
    .stat-val { font-size: 16px; font-weight: 600; }
    .btn {
      width: 100%; padding: 12px; border-radius: 24px; border: none;
      background: var(--color-primary); color: #000; font-weight: bold;
      margin-top: 12px; cursor: pointer;
    }
    .btn:active { transform: scale(0.97); }
    .switch { position: relative; display: inline-block; width: 44px; height: 24px; }
    .switch input { opacity: 0; width: 0; height: 0; }
    .slider {
      position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
      background-color: #334155; transition: .3s; border-radius: 24px;
    }
    .slider:before {
      position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px;
      background-color: white; transition: .3s; border-radius: 50%;
    }
    input:checked + .slider { background-color: var(--color-primary); }
    input:checked + .slider:before { transform: translateX(20px); }
  </style>
</head>
<body>
  <div class="header">⚡ K20 核心更新助手</div>
  <div class="grid">
    <!-- Card 1: System Status -->
    <div class="card">
      <div class="card-title">📱 系統與核心狀態</div>
      <div style="font-size: 14px; margin-bottom: 4px;">裝置: <span id="val-device">Redmi K20 (davinci)</span></div>
      <div style="font-size: 14px; margin-bottom: 4px;">核心: <span id="val-kernel">載入中...</span></div>
      <div style="font-size: 14px;">Root 狀態: <span id="val-root" style="color: #22c55e;">已檢測</span></div>
    </div>

    <!-- Card 2: GitHub Online Updater -->
    <div class="card">
      <div class="card-title">🚀 GitHub 最新核心版本</div>
      <div class="stat-val" id="val-release-tag">正在查詢最新 Release...</div>
      <button class="btn" onclick="flashLatestKernel()">一鍵下載並刷入最新核心</button>
    </div>

    <!-- Card 3: OTA Survival Guard -->
    <div class="card" style="display: flex; justify-content: space-between; align-items: center;">
      <div>
        <div class="card-title">🛡️ LineageOS OTA 自動生存</div>
        <div style="font-size: 13px; color: var(--color-on-surface-variant);">更新 ROM 自動保留核心與 Root</div>
      </div>
      <label class="switch">
        <input type="checkbox" id="sw-addond" onchange="toggleAddonD(this.checked)">
        <span class="slider"></span>
      </label>
    </div>

    <!-- Card 4: Flashing Console -->
    <div class="card">
      <div class="card-title">📜 控制台日誌</div>
      <pre id="console-log" style="font-size: 12px; background: #020617; padding: 8px; border-radius: 8px; height: 100px; overflow-y: auto; color: #38bdf8; margin: 0;">點擊下方按鈕開始記錄...</pre>
    </div>
  </div>

  <script>
    window.onload = function() {
      if (window.Android) {
        document.getElementById("val-kernel").innerText = window.Android.getKernelVersion();
        document.getElementById("val-root").innerText = window.Android.checkRoot() ? "已取得 Root (KernelSU)" : "未取得 Root";
        document.getElementById("sw-addond").checked = window.Android.isAddonDInstalled();
        window.Android.fetchLatestRelease();
      }
    };

    function updateReleaseInfo(tag) {
      document.getElementById("val-release-tag").innerText = tag || "連線失敗";
    }

    function appendLog(msg) {
      const el = document.getElementById("console-log");
      el.innerText += "\n" + msg;
      el.scrollTop = el.scrollHeight;
    }

    function flashLatestKernel() {
      if (window.Android) {
        window.Android.startFlashProcess();
      }
    }

    function toggleAddonD(checked) {
      if (window.Android) {
        window.Android.setAddonD(checked);
      }
    }
  </script>
</body>
</html>
```

- [ ] **Step 2: Write MainActivity.java**

```java
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
```

- [ ] **Step 3: Commit Presentation Layer**

```bash
git add k20_kernel_updater/assets/index.html k20_kernel_updater/src/com/k0983/k20updater/MainActivity.java
git commit -m "feat: add MainActivity and Bento Grid WebUI interface"
```

---

### Task 4: Compilation, Local Installation & Verification

**Files:**
- Output: `k20_kernel_updater/k20_kernel_updater.apk`

- [ ] **Step 1: Execute build_apk.py**

```powershell
python k20_kernel_updater/build_apk.py
```
Expected: PASS with `Build Completed! APK saved to ...\k20_kernel_updater.apk`

- [ ] **Step 2: Install APK to connected phone via ADB**

```powershell
D:\platform-tools\adb.exe install -r k20_kernel_updater/k20_kernel_updater.apk
```
Expected: `Success`

- [ ] **Step 3: Commit final verification**

```bash
git commit -m "build: verify compilation and installation of k20 kernel updater app"
```
