# Redmi K20 (davinci) KernelSU Next

> ⚠️ **此專案是 Vibe Coding** (以 AI 驅動、純憑感覺與默契開發)

本專案專為 Redmi K20 / Mi 9T (`davinci`) 提供 LineageOS Linux 4.14 核心與 KernelSU Next 的編譯與優化支援。

---

## 📱 支援裝置與核心
*   **裝置**：Redmi K20 / Mi 9T (`davinci`)
*   **系統核心**：Linux 4.14 核心 (LineageOS)
*   **Root 方案**：核心級 KernelSU Next (整合 `legacy` 分支，預設使用 Commit `fd093e8b879063aeb0192a3959b0652101ded623`)

---

## ⚡ 核心優化項目
為了確保日常與遊戲的穩定度及流暢度，核心進行了以下優化與配置調整：

1.  **效能編譯優化**：啟用標準 `-O2` 效能編譯參數 (`CONFIG_CC_OPTIMIZE_FOR_PERFORMANCE=y`)，關閉除錯日誌，大幅提升程式執行效率。
2.  **記憶體優化 (ZRAM)**：開啟 ZRAM 優化，並採用高效的 **LZ4 壓縮演算法**，優化虛擬記憶體配置，提升多工背景留存並減少卡頓。
3.  **網路擁塞控制**：整合 **Westwood 網路擁塞控制演算法**，在行動網路與 Wi-Fi 環境下提供更低延遲與更穩定的傳輸率。
4.  **處理器調度與溫控**：優化 CPU 大小核心與 GPU 頻率上限設定，提供流暢的遊戲體驗，同時兼顧日常省電與極佳的發熱控制。
5.  **系統安全與防禦**：預設關閉 KernelSU debug，保持核心乾淨，提升系統安全防護。

---

## ⚠️ 注意事項與免責聲明
在刷入或使用此核心前，請務必詳閱以下注意事項：

1.  **刷機風險與備份**：修改核心引導分區（Boot）存在一定風險。刷入前**請務必備份原廠的 Boot 映像檔**，以便在發生 Bootloop（無限重啟）時能隨時透過 Fastboot 或 Recovery 還原。
2.  **DTBO 分區安全**：Redmi K20 在 LineageOS 中使用獨立的 DTBO 分區。通常情況下**只需刷入核心 ZIP 即可，切勿隨意單獨刷入 `dtbo.img`**，以避免觸控螢幕失效或開機死機。
3.  **上游版本相容性**：專案採用特定的 KernelSU Next legacy 提交。不建議盲目追蹤上游最新分支，以免破壞舊版 Linux 4.14 核心的編譯相容性。
4.  **免責聲明**：本專案基於個人樂趣與 Vibe Coding 開發，不提供任何形式的保固。若因使用本核心導致硬體損壞、資料遺失或鬧鐘沒響，作者概不負責。

---

## 🔒 安全、隱私與開源授權說明
為維護專案安全性、隱私以及符合開源法律規範，請務必注意以下開發事項：

1.  **敏感資訊防洩漏與 Git Commit 歷史**：
    *   在進行 `git commit` 前，請務必使用 `git status` 或 `git diff` 仔細檢查是否夾帶敏感資料（如 API Token、私密金鑰或個人備忘錄）。
    *   **注意**：Git 會忠實記錄每一次修改。即使在最新版本中將檔案刪除，任何人依然能透過 Commit History 歷史紀錄翻找並下載該檔案。
2.  **Git 提交者郵件與隱私保護**：
    *   若你的電腦上 Git 設定的 `user.email` 包含真實姓名或常用的生活信箱，Push 至 GitHub 後將會對全世界公開。
    *   **建議**：可至 GitHub 設定（Settings ➜ Emails）勾選 **Keep my email addresses private**。將 GitHub 提供給你的專屬匿名信箱設定至本機 Git 內，即可完美隱匿真實信箱。
3.  **避免程式碼中包含本地絕對路徑**：
    *   在修改或編譯腳本、Makefile、defconfig 時，請勿寫入包含你本地電腦的「絕對路徑」（例如 `/home/charlie/...`），這會直接曝露你電腦中的使用者名稱。請一律使用相對路徑。
4.  **Linux 核心開源協議 (GPLv2)**：
    *   Linux 核心採用 **GPLv2**（通用公共授權條款第二版）協議授權。
    *   依協議規定，GPLv2 具有「傳染性」：任何對核心原始碼進行修改、客製的二次開發作品，都必須強制以 GPLv2 協議公開釋出其完整的原始碼。本專案嚴格遵循此開源合規義務。

---

## ⚖️ 開源協議 (License)
本專案採用 [GNU General Public License v2.0 (GPLv2)](file:///d:/googleAI/redmi-k20-kernel-builder/LICENSE) 授權協議進行開源。
