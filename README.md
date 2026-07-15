# Redmi K20 (davinci) LineageOS 23.2 KernelSU Next Builder

這個 repository 使用 GitHub Actions 編譯 Redmi K20 / Mi 9T (`davinci`) 的
LineageOS 23.2 Linux 4.14 核心，整合針對舊核心維護的 KernelSU Next
`legacy` 分支。

## 一鍵編譯

1. 將修改 push 到 GitHub repository。
2. 進入 GitHub 的 **Actions** 頁面。
3. 選擇 **Build Redmi K20 Kernel**。
4. 按下 **Run workflow**。
5. 一般情況保留預設值：
   - `kernel_ref`: `lineage-23.2`
   - `ksun_ref`: `fd093e8b879063aeb0192a3959b0652101ded623`
   - `build_dtbo`: `true`
6. 完成後從該 workflow run 的 **Artifacts** 下載結果。

預設的 `ksun_ref` 是已檢查過的 KernelSU Next legacy commit，讓建置結果可重現。
想測試 legacy 分支當下的最新版本時，可以把它改成 `legacy`；測試成功後再將
workflow 的預設 commit 更新成該次 `build-info.txt` 記錄的 `ksun_commit`。不建議
永遠無條件追蹤最新 commit，因為上游變更仍可能破壞 Linux 4.14 相容性。

## 輸出

- `AnyKernel3-davinci-KernelSU-Next-kernel-only.zip`：只替換 boot 核心，建議先刷。
- `Image.gz`：單獨的核心映像。
- `dtbo-davinci.img`：獨立的 davinci DTBO 分區映像，page size 為 4096。
- `dtbo-info.txt`：DTBO 表格資訊。
- `kernel.config`：這次實際使用的核心設定。
- `build-info.txt`：LineageOS 與 KernelSU Next 的 ref、commit、版本資訊。
- `SHA256SUMS`：所有 release 檔案的 SHA-256。

## KernelSU Next 整合方式

- 使用 KernelSU Next `legacy`，不是已移除部分 4.x 支援的最新正式版分支。
- 使用 manual hooks，明確停用 kprobes hooks。
- KernelSU Next 保持為獨立 Git repository，讓其 Kbuild 可以產生正確的版本號。
- AnyKernel3 固定在 commit `1c9a500dd4aa8081952523126e97eb155aed941b`，只產出
  不修改 `/vendor/lib/modules` 的 kernel-only ZIP。
- classic hooks 工具固定在 commit
  `9e30076418813fc7eaab6481da2e745dfde56249`，避免上游變動造成不可重現的建置。
- 套用 classic hooks 時排除 Next legacy 已不再提供 handler 的舊 `devpts` hook，
  避免直到 `vmlinux` 連結階段才出現 undefined reference。
- `patch_manual_hooks.py` 補上 vendor Linux 4.14 所需的 namespace 宣告，以及
  KernelSU Next supercall 使用的 reboot hook；插入點不符合預期時會直接停止建置。
- `patch_ksun_legacy.py` 修正 SULog 在 Linux 4.14 的 boottime `timespec` 型別，
  並處理此 vendor kernel 已回移 `__poll_t` 所造成的重複 typedef。
- SUSFS 目前未啟用。先確認核心可編譯、可開機且 root/模組正常，再另外移植。

## DTBO 與刷入安全

LineageOS davinci 使用獨立 DTBO 分區。AnyKernel ZIP 不會自動刷入
`dtbo-davinci.img`。

只刷 kernel-only ZIP，不另外刷 DTBO。只有在已備份原始 DTBO、確認可進入
fastboot/recovery 並知道如何還原後，才另外測試 `dtbo-davinci.img`；不同 ROM
或 firmware 的 DTBO 不一定能互換。

刷包在完成 boot 寫入後會執行 `sync`，再以明確的成功狀態退出，讓 recovery
返回操作畫面。它不會自動重新開機。若仍停在 `Done!`，代表該 recovery 的 UI
沒有接收退出狀態；此時 boot 已寫入，不需要重複刷入。

## 安全效能設定

核心會明確使用標準 `CONFIG_CC_OPTIMIZE_FOR_PERFORMANCE=y` (`-O2`) 並停用
KernelSU debug。其餘排程、CPU governor、scheduler statistics 與 workqueue 設定
維持 LineageOS davinci 原始 defconfig，避免實驗性設定造成開機相容性問題。

此建置不加入超頻、降壓，不修改 CPU/GPU 最高頻率、頻率表或 thermal 控制。
