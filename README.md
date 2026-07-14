# Redmi K20 (davinci) LineageOS 23.2 SukiSU Ultra Builder

這個 repository 透過 GitHub Actions 建置 Redmi K20 / Mi 9T (`davinci`) 的
LineageOS 23.2 Linux 4.14 核心，並整合最新「穩定版」SukiSU Ultra。

## 一鍵建置

1. 將修改 push 到 GitHub repository。
2. 進入 GitHub 的 **Actions** 頁面。
3. 選擇 **Build Redmi K20 Kernel**。
4. 按 **Run workflow**。
5. 一般情況保持以下預設值即可：
   - `kernel_ref`: `lineage-23.2`
   - `sukisu_ref`: `latest`
   - `build_dtbo`: `true`
6. 完成後在該次 workflow 的 **Artifacts** 下載建置結果。

`sukisu_ref=latest` 會在每次按下按鈕時查詢並使用 SukiSU Ultra 最新的正式
release；若要測試特定版本，可填入例如 `v4.1.3`，若要測試開發版則填
`main`。開發版可能在上游重構後暫時無法套用舊核心相容修補。

## 產物

- `AnyKernel3-davinci-SukiSU-Ultra.zip`：刷入 boot 分區的核心 ZIP。
- `Image.gz`：未打包的核心映像。
- `dtbo-davinci.img`：獨立的 davinci DTBO 分區映像（4096-byte page）。
- `dtbo-info.txt`：DTBO 表格內容，方便檢查及後續優化。
- `kernel.config`：本次實際使用的完整核心設定。
- `build-info.txt`：LineageOS 與 SukiSU 的實際 ref、commit。
- `SHA256SUMS`：所有產物的 SHA-256。

## DTBO 與刷入安全

LineageOS 的官方 davinci 裝置設定使用純 `Image.gz`、boot image 內的獨立 DTB
欄位，以及獨立 `dtbo` 分區。因此 AnyKernel ZIP 只替換核心，會保留目前 boot
image 的 DTB；`dtbo-davinci.img` 不會被 ZIP 自動刷入。

第一次測試時建議只刷 AnyKernel ZIP。只有在已備份原始 `dtbo`、確認能進
fastboot/recovery 並理解還原方法後，才另外測試 `dtbo-davinci.img`。不同 ROM
或 firmware 的 DTBO 不一定可以互換。

## 失敗診斷

如果建置失敗，workflow 會上傳 `davinci-build-failure-diagnostics`，內容包含：

- `build.log`
- 實際的 `.config`
- 上游版本資訊
- 任何未成功套用的 `.rej` patch

相容修補器採嚴格模式；如果新版 SukiSU 改動了被修補的程式碼，workflow 會
在整合階段清楚失敗，而不是繼續產生可能不完整或無法開機的映像。

## SUSFS 狀態

目前流程先不啟用 SUSFS。舊流程只套用了 `susfs4ksu` 的核心檔案系統 patch，
卻沒有套用 KernelSU 端的控制與 Kconfig patch；而 4.14 分支提供的 KernelSU
patch 又是舊目錄結構，不能直接套到 SukiSU Ultra 4.1.x。這會形成「看似已
啟用，實際上功能不完整」的核心。應先確認目前 SukiSU、boot 與 DTBO 均穩定，
之後再針對新版 SukiSU API 單獨移植及測試 SUSFS。
