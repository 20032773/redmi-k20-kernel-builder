# Redmi K20 核心更新助手 架構與設計規格書 (Design Spec)

**日期：** 2026-07-24  
**應用包名：** `com.k0983.k20updater`  
**專案性質：** 私人個人專用工具 (Private Personal Tool - 本地開發不推送到 GitHub)  
**目標裝置：** Redmi K20 / Mi 9T (`davinci`)  
**目標系統：** LineageOS 23.2（或具備 LineageOS Updater / `addon.d` 生存腳本支援之第三方 ROM）  

---

## 1. 摘要與開發目標

### 🎯 開發目標
- **OTA 自動生存機制**：提供 `addon.d` 腳本管理功能，防止 LineageOS 系統 OTA 更新後丟失客製化 K20 核心與 KernelSU-Next Root 權限。
- **一鍵連網更新核心**：讓使用者直接透過 Root 權限查詢、下載並刷入指定 GitHub Releases (`20032773/redmi-k20-kernel-builder`) 最新編譯好的 AnyKernel3 刷機包。
- **分層解耦架構 (Clean Architecture)**：完全沿用 `ai-ledger-app` 記帳專案的四層架構（UI 介面 / Domain 領域業務 / Data 資料庫與 API / Core 底層核心）。
- **Material You Bento Grid 介面**：提供現代化微醺玻璃（Liquid Glass）、動態取色與彈性觸覺（Haptic Feedback）回饋的便當盒網格儀表板。
- **私人專屬與隱私保護**：本 App 專碼專用，僅在本地端進行編譯安裝，不會推送至任何公開 GitHub 倉庫。

### 🚫 非目標 (Non-Goals)
- 支援不具備 `addon.d` 腳本機制的第三方 ROM。
- 在手機本機直接編譯 Linux 核心（核心編譯由 GitHub Actions 自動化處理）。
- 將本 App 的原始碼推送到公開的 GitHub 倉庫。

---

## 2. 系統架構與分層設計

本應用採用標準的四層 Clean Architecture 解耦架構：

```
+-------------------------------------------------------------+
|                     Presentation UI 介面層                  |
| (Jetpack Compose / M3 Bento Grid 網格, ViewModels, StateFlow)|
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                        Domain 業務領域層                    |
|    (UseCases: CheckUpdate, FlashKernel, ToggleAddonD)       |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                         Data 資料處理層                     |
|  (KernelRepository, AddonDRepository, GitHubReleaseApi)     |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                         Core 底層核心層                     |
|    (SuShellExecutor, NetworkClient, HapticFeedbackUtils)    |
+-------------------------------------------------------------+
```

### 各層職責說明

1. **`core`（底層核心層）**
   - `SuShellExecutor`：處理 Root (`su`) 高權限指令執行，支援行串流（Line-by-line streaming）即時顯示 AnyKernel3 刷入過程日誌。
   - `GitHubReleaseClient`：對 `https://api.github.com/repos/20032773/redmi-k20-kernel-builder/releases/latest` 發送 REST GET 請求。
   - `HapticUtils`：管理系統觸覺回饋（按鍵輕觸、刷入成功雙重震動、失敗警告震動）。

2. **`data`（資料處理層）**
   - `KernelRepositoryImpl`：整合 `/proc/version` 本地核心資訊、`getprop` 系統版本、Root 狀態與 GitHub 遠端 Release 元資料。
   - `AddonDRepositoryImpl`：管理 `/system/addon.d/99-k20-kernel.sh` 腳本與 `/data/adb/k20_kernel_backup.zip` 備份檔。

3. **`domain`（業務領域層）**
   - `GetSystemStatusUseCase`：取得當前 Linux 核心版本字串、LineageOS 版本號、Root 授權狀態與 `addon.d` 防護狀態。
   - `CheckKernelUpdateUseCase`：比對本地編譯日期與 GitHub 最新 Release 標籤日期。
   - `FlashKernelUseCase`：負責下載 AnyKernel3 zip 檔、於 Root 環境解包執行 `anykernel.sh`（或寫入 `boot` 分區），並在完成後執行 `sync` 檔案寫入快取。
   - `ToggleAddonDUseCase`：於 `/system/addon.d/99-k20-kernel.sh` 寫入或移除 OTA 自動生存腳本。

4. **`ui`（介面展示層）**
   - `MainViewModel`：透過 `StateFlow<MainUiState>` 提供單向資料流 UI 狀態控制。
   - `HomeScreen`：頂層 Bento Grid 儀表板，包含 4 個半透明 Material 3 卡片。

---

## 3. 詳細組件與 UI 設計 (Bento Grid 網格)

主儀表板由 4 個 Bento Grid 卡片組成：

### 卡片 1：當前系統與核心狀態 (System Status)
- **裝置代號**：`Redmi K20 / davinci`
- **系統版本**：LineageOS 分支與版本字串
- **核心版本**：當前運行的 Linux 核心版本字串（讀自 `/proc/version`）
- **Root 狀態**：綠色顯示 `KernelSU-Next 已激活` 或 `已取得 Root 權限`；若未取得則顯示警告標籤

### 卡片 2：GitHub 最新核心與一鍵更新 (GitHub Updater)
- **最新版本標示**：顯示 GitHub 最新 Release 標籤（如 `RedmiK20-davinci-lineageos23.2-20260724-KernelSU-Next`）
- **動作按鈕**：「一鍵連網下載並刷入最新核心」
- **刷入彈窗**：點擊後彈出即時主控台視窗，滾動顯示 AnyKernel3 刷入過程日誌

### 卡片 3：LineageOS OTA 生存防護 (`addon.d` Guard)
- **開關切換**：「LineageOS OTA 更新自動保留核心與 Root」
- **運作原理**：
  - 開啟時自動複製 `99-k20-kernel.sh` 腳本至 `/system/addon.d/`，並將最新 AnyKernel3 zip 快取於 `/data/adb/k20_kernel_backup.zip`。
  - 當 LineageOS Updater 完成 OTA 更新重啟前，系統會自動調用 `99-k20-kernel.sh` 將新刷好的 `boot` 分區自動重新補上 K20 客製核心與 Root！

### 卡片 4：刷入日誌與觸覺控制 (Logs & Settings)
- **日誌檢視器**：可展開查看最近一次刷入歷程的控制台 Log。
- **重新整理按鈕**：手動重新讀取系統狀態與 GitHub 最新版本。
- **觸覺開關**：開啟/關閉按鈕點擊與狀態切換時的微震動回饋。

---

## 4. 安全機制與例外處理 (Safety & Resilience)

1. **Root 權限雙重校驗**：
   - App 啟動時即自動檢測 `su` 權限。若使用者未授權，自動停用一鍵刷入與 `addon.d` 設定，並顯示提示 Banner。
2. **下載完整性校驗**：
   - 下載 AnyKernel3 zip 時同時拉取 `SHA256SUMS`，校驗雜湊值無誤後才執行寫入操作。
3. **分區寫入安全保證**：
   - AnyKernel3 執行完成後立即呼叫 `sync` 強制刷新系統緩存。
   - 刷寫進行中自動鎖定 UI 與返回鍵，防止刷寫中途退出。

---

## 5. 驗證與測試計畫

### 自動化檢查
- 驗證 `SuShellExecutor` 在執行 `su` 指令時能正確回傳 0 返回碼。
- 驗證 GitHub REST API 回傳 JSON 格式之解析正確性。

### 手動實機驗證
- 在搭載 KernelSU-Next 的 Redmi K20 上測試 Root 提權與選色介面。
- 測試一鍵連網下載與 AnyKernel3 本地刷寫。
- 模擬 LineageOS OTA 更新測試 `addon.d` 生存腳本復原結果。
