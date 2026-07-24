# Redmi K20 Kernel Updater Architecture & Design Spec

**Date:** 2026-07-24  
**Package:** `com.k0983.k20updater`  
**Target Device:** Redmi K20 / Mi 9T (`davinci`)  
**Target ROM:** LineageOS 23.2 (or compatible custom ROMs with LineageOS Updater / `addon.d` support)  

---

## 1. Executive Summary & Goals

### Goals
- **Automated OTA Survival**: Provide an `addon.d` script management system to prevent losing custom kernel modifications and KernelSU-Next Root after LineageOS system updates.
- **One-Click Online Kernel Update**: Enable users to check, download, and flash the latest compiled AnyKernel3 zip directly from GitHub Releases (`20032773/redmi-k20-kernel-builder`) using Root permissions.
- **Clean Architecture**: Follow the established `ai-ledger-app` architecture (Clean Architecture: UI / Domain / Data / Core separation).
- **Material You Bento Grid UI**: Deliver a modern, translucent, dynamic-colored Bento Grid dashboard UI with tactile haptic feedback.

### Non-Goals
- Supporting non-LineageOS ROM update mechanisms that lack `addon.d` survival support.
- Building custom kernels directly on the device (kernel compilation remains on GitHub Actions).

---

## 2. Architecture & Layering

The application follows a clean 4-layer architecture:

```
+-------------------------------------------------------------+
|                     Presentation Layer                      |
| (Jetpack Compose / M3 Bento Grid UI, ViewModels, StateFlow) |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                        Domain Layer                         |
|    (UseCases: CheckUpdate, FlashKernel, ToggleAddonD)       |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                         Data Layer                          |
|  (KernelRepository, AddonDRepository, GitHubReleaseApi)     |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                         Core Layer                          |
|    (SuShellExecutor, NetworkClient, HapticFeedbackUtils)    |
+-------------------------------------------------------------+
```

### Layer Breakdown

1. **`core`**
   - `SuShellExecutor`: Handles elevated shell commands via `su`. Streams command output line-by-line for live execution logging.
   - `GitHubReleaseClient`: REST client that queries `https://api.github.com/repos/20032773/redmi-k20-kernel-builder/releases/latest`.
   - `HapticUtils`: Manages device vibration patterns for button presses and flashing completion.

2. **`data`**
   - `KernelRepositoryImpl`: Provides system status (from `/proc/version`, `getprop`, and Root check), checks local storage for cached AnyKernel3 zips, and fetches GitHub Release metadata.
   - `AddonDRepositoryImpl`: Manages `/system/addon.d/99-k20-kernel.sh` and `/data/adb/k20_kernel_backup.zip`.

3. **`domain`**
   - `GetSystemStatusUseCase`: Returns current kernel string, LineageOS version, Root status, and `addon.d` protection status.
   - `CheckKernelUpdateUseCase`: Compares local build date against GitHub latest release metadata.
   - `FlashKernelUseCase`: Handles downloading the latest AnyKernel3 zip, unzipping inside Root environment, running `anykernel.sh` or writing `Image.gz` to the `boot` partition, and performing storage syncs.
   - `ToggleAddonDUseCase`: Installs or removes the `99-k20-kernel.sh` OTA survival script using Root privileges.

4. **`ui`**
   - `MainViewModel`: Exposes `StateFlow<MainUiState>` for atomic UI updates.
   - `HomeScreen`: Top-level Bento Grid layout containing 4 translucent Material 3 cards.

---

## 3. Detailed Component & UI Design (Bento Grid)

The main dashboard consists of 4 Bento Grid Cards:

### Card 1: System Status (系統狀態)
- **Device Info**: Device codename (`Redmi K20 / davinci`).
- **OS Version**: LineageOS branch/version string.
- **Kernel Version**: Currently running Linux kernel version string (from `/proc/version`).
- **Root Status**: Badge showing `KernelSU-Next Active` or `Root Granted` in green, or warning badge if Root is missing.

### Card 2: GitHub Online Updater (GitHub 一鍵更新)
- **Latest Release Display**: Shows GitHub latest tag (e.g. `RedmiK20-davinci-lineageos23.2-20260724-KernelSU-Next`).
- **Update Action Button**: "一鍵連網下載並刷入最新核心".
- **Flash Dialog**: Opens an interactive modal showing line-by-line log output during AnyKernel3 execution.

### Card 3: LineageOS OTA Survival Guard (`addon.d` 生存防護)
- **Toggle Switch**: "LineageOS OTA 更新自動保留核心與 Root".
- **Functionality**:
  - When enabled, copies `/system/addon.d/99-k20-kernel.sh` and caches the latest AnyKernel3 zip at `/data/adb/k20_kernel_backup.zip`.
  - During a LineageOS system update, `99-k20-kernel.sh` is automatically called post-install to patch the updated `boot` partition before rebooting.

### Card 4: Flashing Logs & Settings (日誌與設定)
- **Log Viewer**: Expandable console output showing previous flashing session logs.
- **Refresh Button**: Manual pull/click to re-check system status and GitHub API.
- **Haptic Toggle**: Enable/disable custom tactile vibration feedback.

---

## 4. Safety & Edge Cases

1. **Root Verification**:
   - App checks for Root access on startup. If Root is denied, flashing and `addon.d` toggles are gracefully disabled with an explanatory banner.
2. **Download Integrity**:
   - Downloads `SHA256SUMS` along with the AnyKernel3 zip and verifies SHA-256 hash before executing any flash commands.
3. **Partition Write Safety**:
   - Ensures `sync` is called immediately after AnyKernel3 completes.
   - Prevents app closure or system reboot while flashing is in progress.

---

## 5. Verification & Test Plan

### Automated Checks
- Verify `SuShellExecutor` returns 0 exit code on standard root commands.
- Verify JSON parsing of GitHub API response.

### Manual Verification
- Test Root permission request on Redmi K20 with KernelSU-Next.
- Test downloading and flashing AnyKernel3 zip locally.
- Test `addon.d` survival by simulating a LineageOS OTA update.
