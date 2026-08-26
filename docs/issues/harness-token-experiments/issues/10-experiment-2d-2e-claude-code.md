# 10: Experiment 2d–2e — Claude Code 上的 pass by reference

**What to build:** 在 Claude Code 上比較兩種資料傳遞方式：資料置於 sandbox 由 pandas 取用，對照資料以文字全量塞入。沿用 09 建立的資料分析任務，驗證同樣的原理在既有工具上是否成立。

**Blocked by:** 07, 09

**Status:** in-progress

- [x] 沿用 09 的資料分析任務與判準
- [ ] 2d、2e 各三次 run
- [x] Run 紀錄透過 07 的 adapter 產出
- [ ] 2e 需刻意將資料以文字全量置入，而非依賴 Claude Code 的預設行為
- [ ] 結果與 2a–2c 分開呈現，不與自建 harness 的百分比合併

## Comments

**這張票需要一個本 harness 無法自己發動的步驟：驅動另一個 Claude Code session。**
那等於這個 session 要 spawn 自己的複本，做不到，也不該做。範圍因此劃在「素材產生」與
「transcript 評分」兩端，中間那段（實際跑三次 2d、三次 2e）留給操作者手動執行，程序寫在
`pass_by_reference_claude_code.py` 的模組 docstring：起 session → 貼上對應 prompt →
記下 transcript 路徑 → 呼叫 `grade_transcript`。

已完整驗證（不需真的跑 Claude Code）：

- 2e 的 prompt 把資料集**每一列的 amount** 都以文字形式包含在內，逐列斷言、不是抽樣。
- 2d 的 prompt 只提到檔名，完全不含任何一列的 amount 值——差異就是題目要測的東西本身。
- CSV 檔案確實寫到磁碟供 2d 的 session 讀取。
- `grade_transcript` 對著手工建構、格式與真實 transcript 相同的樣本測過：答對判 pass、
  答錯判 fail。

沿用 09 的資料集生成與正解計算（`generate_orders`、`top_customer_by_total`），沒有重新
發明一套——兩邊測的是同一個問題，只是遞送資料的方式不同。

`claude_code_adapter` 新增 `final_assistant_text`：session 的最後一輪往往只有 tool_use
沒有文字（例如結尾又跑了一次 bash），要抓的是**最後一個有說話的 assistant turn**，不是
單純的最後一行。
