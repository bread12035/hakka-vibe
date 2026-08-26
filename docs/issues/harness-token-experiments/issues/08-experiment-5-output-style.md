# 08: Experiment 5a–5c — output style

**What to build:** 比較無 style、caveman、STE100 三者在主任務上的 output token 與成本。以 output token 衡量而非 cache token：output style 影響模型寫出的內容，其指令本身是一小段靜態文字。

**Blocked by:** 04, 05

**Status:** in-progress

- [x] 5a、5b、5c 各三次 run
- [ ] 以 output token 為主要觀察對象，成本仍以美元表述
- [x] caveman 與 STE100 分列為獨立 arm，不合併為「有 style」
- [ ] 報告各 arm 的 pass/fail 次數，確認精簡輸出未損及任務完成
- [x] 更換 style 僅替換一段 system prompt 文字，不建置可插拔架構

## Comments

**狀態為 in-progress：九次付費呼叫未執行。**

機制（`OutputStyle`、附加而非改寫 frozen system block）在 ticket 06 就已建好並驗證，
本票只是把它接成 `5a`/`5b`/`5c` 三個 arm。已驗證：baseline 不帶任何 style 指令；
caveman 與 STE100 是相異的兩個 instruction，不會被合併成同一個「有 style」的 arm。

以 output token 衡量、非 cache token 這條，機制上已成立——style 只是附加在 frozen system
block 之後的一小段穩定文字，本身會被 cache，不影響 cache 行為；它改變的是模型寫出多少字，
量測會在 `RunRecord.tokens.output` 上直接讀到，不需要額外機制。

`_fresh_copy` 在本票開發時發現與 ticket 06 完全重複，已抽成 `experiment.fresh_copy_of`
共用；兩個模組因此都改了 import。
