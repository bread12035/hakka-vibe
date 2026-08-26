# 11: Experiment 1a–1e — prompt 排序

**What to build:** 讓 prompt 的組裝順序可替換，比較 static 內容、對話紀錄、dynamic 內容的不同排列如何影響 cache，並觀察 compact 觸發後的變化。TTL 選擇作為子項一併測試。僅在自建 harness 執行：Claude Code 的組裝順序不可控，無對照組。

**Blocked by:** 04, 05

**Status:** ready-for-agent

- [ ] Prompt 組裝順序成為可替換的 seam，由本 experiment 的多個 arm 驅動產生
- [ ] 1a 至 1e 各三次 run
- [ ] 報告各 arm 的 cache read 與 cache write 比例，顯示哪些排列打翻了 cache
- [ ] 1d 持續執行至 compact 觸發，記錄其對 cache 的影響
- [ ] 1e 與 1a 唯一差異為 TTL，據以判斷 1 小時 TTL 的雙倍寫入成本是否換到對應的命中率
