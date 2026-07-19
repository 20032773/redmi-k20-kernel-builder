# Redmi K20 (davinci) KernelSU Next

本專案專為 Redmi K20 / Mi 9T (`davinci`) 提供 LineageOS Linux 4.14 核心與 KernelSU Next 的編譯與優化支援。

---

## 📱 支援裝置與核心
*   **裝置**：Redmi K20 / Mi 9T (`davinci`)
*   **系統核心**：Linux 4.14 核心 (LineageOS)
*   **Root 方案**：核心級 KernelSU Next (整合 `legacy` 分支與 manual hooks)

---

## ⚡ 核心優化項目
為了確保日常與遊戲的穩定度及流暢度，核心進行了以下優化與配置調整：

1.  **效能編譯優化**：啟用標準 `-O2` 效能編譯參數 (`CONFIG_CC_OPTIMIZE_FOR_PERFORMANCE=y`)，關閉除錯日誌，大幅提升程式執行效率。
2.  **記憶體優化 (ZRAM)**：開啟 ZRAM 優化，並採用高效的 **LZ4 壓縮演算法**，優化虛擬記憶體配置，提升多工背景留存並減少卡頓。
3.  **網路擁塞控制**：整合 **Westwood 網路擁塞控制演算法**，在行動網路與 Wi-Fi 環境下提供更低延遲與更穩定的傳輸率。
4.  **處理器調度與溫控**：優化 CPU 大小核心與 GPU 頻率上限設定，提供流暢的遊戲體驗，同時兼顧日常省電與極佳的發熱控制。
5.  **系統安全與防禦**：預設關閉 KernelSU debug，保持核心乾淨，提升系統安全防護。
