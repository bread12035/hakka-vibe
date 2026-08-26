# 12: Experiment 4a–4b — 動態 tool 選擇

**What to build:** 配置一個暴露遠多於所需 tool 的任務，比較全部 tool 直接暴露與 tool search 搭配延遲載入。兩個 harness 皆執行。

**Blocked by:** 04, 05, 07

**Status:** in-progress

- [x] 任務暴露的 tool 數量遠多於實際需要，實際只需其中少數
- [ ] 4a、4b 各三次 run，兩個 harness 分別執行
- [ ] 報告 tool 定義本身佔用的 token，以及它對 cache write 的影響
- [ ] 報告各 arm 的 pass/fail 次數，確認延遲載入未導致模型找不到需要的 tool
- [ ] 兩個 harness 的結果分開呈現

## Comments

**狀態為 in-progress：6 次付費呼叫（自建 harness 2 arm × 3 次）未執行；Claude Code 那半
是操作者手動步驟，同 ticket 10 的模式。**

自建 harness 已驗證（無需呼叫）：`decoy_tools.generate_decoy_tools` 產生 30 個確定性、
從未被真正呼叫的假 tool，用來把 tool 清單灌大。4a 直接全部暴露；4b 把同一批 decoy 全部
標上 `defer_loading: true`，接上 `tool_search_tool_bm25_20251119`，並確認：

- search tool 本身**不能**被 defer（API 規則：deferred 的話會 400 `All tools have
  defer_loading set`）
- 任務真正需要的四個能力（`list_files`／`read_file`／`write_file`／`run_tests`）保持
  non-deferred——它們每輪都用得到，不是「查一下才需要」的東西
- 30 個 decoy 全部且只有它們被標記 deferred

Claude Code 那半沒有另外寫程式碼：掛多少 MCP tool 是操作者在啟動 session 時決定的
設定，不是這個 harness 能從內部控制的參數。程序是——4a 用一個掛了大量 MCP server 的
session 跑任務；4b 用同樣任務但改用較少 MCP server（或啟用 tool search，如果 Claude Code
支援）；兩者結束後都用 07 的 `run_record_from_transcript` 讀 transcript，比較**第一輪的
`cache_creation_input_tokens`**——那大致是 tool 定義本身佔用的 token 量。這條沿用既有
adapter，沒有引入新機制。
