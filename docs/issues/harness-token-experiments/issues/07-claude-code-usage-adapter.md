# 07: Claude Code usage adapter

**What to build:** 解析 Claude Code 的 session transcript，產出與自建 harness 同型的 run 紀錄。Claude Code 的 transcript 已含每次呼叫的完整 usage，包括 thinking token 與依 TTL 分流的 cache write，因此不需要額外的遙測設定。

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] 從 session transcript 產出 run 紀錄，型別與自建 harness 相同
- [ ] 這是 RunRecord 建構的第二個 adapter，使該 seam 具備兩個真實 adapter
- [ ] 套用 1 小時 TTL 的 cache write 單價，因 Claude Code 的 TTL 不可設定
- [ ] 解析邏輯有測試覆蓋，測試不需要網路
- [ ] 報告輸出時標明兩個 harness 的百分比不可跨比
