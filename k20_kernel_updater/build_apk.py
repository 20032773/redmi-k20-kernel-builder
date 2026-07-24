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
