# 11: Experiment 1a–1e — prompt 排序

**What to build:** 讓 prompt 的組裝順序可替換，比較 static 內容、對話紀錄、dynamic 內容的不同排列如何影響 cache，並觀察 compact 觸發後的變化。TTL 選擇作為子項一併測試。僅在自建 harness 執行：Claude Code 的組裝順序不可控，無對照組。

**Blocked by:** 04, 05

**Status:** in-progress

- [x] Prompt 組裝順序成為可替換的 seam，由本 experiment 的多個 arm 驅動產生
- [ ] 1a 至 1e 各三次 run
- [ ] 報告各 arm 的 cache read 與 cache write 比例，顯示哪些排列打翻了 cache
- [ ] 1d 持續執行至 compact 觸發，記錄其對 cache 的影響
- [ ] 1e 與 1a 唯一差異為 TTL，據以判斷 1 小時 TTL 的雙倍寫入成本是否換到對應的命中率

## Comments

**狀態為 in-progress：15 次付費呼叫未執行，且 1d 是否真的觸發 compact 需要實際跑很長的
對話才能觀察，此環境無法驗證。**

Frozen 的 static 內容（system prompt）不受任何排列影響——API 固定用 `tools → system →
messages` 組裝，這段沒有 seam 可放。真正能動的是 `messages` 陣列內 **dynamic 內容相對
於 history 的位置**，這才是 `prompt_layout.assemble_messages` 這個純函數在測的東西：

- 1a：history 全部在前，dynamic note 放最後——它是最新的東西，放最後才不會讓前面已經
  cache 過的 byte 被打斷。
- 1b：dynamic note 放最前——它每輪都變，變的東西擋在最前面，等於讓後面全部失效。
- 1c：把一段固定提醒穿插進 history 之間。這個安排**只對全新對話有利**：一旦插入，之後
  每一輪的 byte 都跟插入前 cache 過的版本不同，對「接續中」的對話反而是負分。這條在
  docstring 裡直接寫死，提醒之後看數據的人。

`_dynamic_note()` 刻意設計成**衍生自 agent 狀態**（輪數／budget），不是模型可寫的欄位——
這樣它的內容是確定的，排列方式才可能在沒有真的呼叫的情況下被測試。已有一條測試接進
`FixerAgent.messages_for_test`，證實 `prompt_layout` 設定真的改變了組出來的 messages
順序，不是死欄位。

1d 開啟 server-side compaction：`client.beta.messages.create` + `betas=["compact-2026-01-12"]`
+ `context_management={"edits": [{"type": "compact_20260112"}]}`，形狀取自 API 文件，
非憑記憶重建（依 `claude-api` skill 的規則核對過）。

1e 除了 TTL 跟 1a 完全一樣，是乾淨的單變因對照。

再次出現與前兩張票相同的重複：`_fresh_copy` 又被重新寫了一次，已改回呼叫共用的
`experiment.fresh_copy_of`。
