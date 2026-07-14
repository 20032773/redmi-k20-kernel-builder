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

- `AnyKernel3-davinci-KernelSU-Next.zip`：刷入 boot 分區的核心 ZIP。
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
- classic hooks 工具固定在 commit
  `9e30076418813fc7eaab6481da2e745dfde56249`，避免上游變動造成不可重現的建置。
- `patch_manual_hooks.py` 補上 vendor Linux 4.14 所需的 namespace 宣告，以及
  KernelSU Next supercall 使用的 reboot hook；插入點不符合預期時會直接停止建置。
- SUSFS 目前未啟用。先確認核心可編譯、可開機且 root/模組正常，再另外移植。

## DTBO 與刷入安全

LineageOS davinci 使用獨立 DTBO 分區。AnyKernel ZIP 只替換 boot 裡的核心，
不會自動刷入 `dtbo-davinci.img`。

第一次測試建議只刷 AnyKernel ZIP。只有在已備份原始 DTBO、確認可進入
fastboot/recovery 並知道如何還原後，才另外測試 `dtbo-davinci.img`。不同 ROM
或 firmware 的 DTBO 不一定能互換。

## 失敗診斷

如果編譯失敗，workflow 會上傳 `davinci-build-failure-diagnostics`，可能包含：

- `build.log`
- `build-info.txt`
- 核心 `.config`
- patch reject (`.rej`) 檔案

把新的 Actions log 或失敗診斷 artifact 放進 `D:\googleAI\logs`，即可繼續定位。
