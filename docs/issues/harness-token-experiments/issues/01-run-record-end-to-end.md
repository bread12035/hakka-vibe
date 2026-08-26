# 01: 單次呼叫的成本記錄

**What to build:** 對模型發出一次呼叫，把回傳的 usage 換算成美元，寫成一份 run 紀錄落地。沒有 agent，沒有 fixture，只有「呼叫一次、算出錢、存起來」這條最薄的完整路徑。計價算術與紀錄格式在此定案，後續 72 次 run 全部沿用。

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] 一次呼叫的 usage 被完整保留：input、output、thinking token、cache read、依 TTL 分流的 cache write、逐輪明細
- [ ] Cost model 依 ADR-0002 換算：cache read 0.1×、input 1×、cache write 5m 1.25×、cache write 1h 2×、output 5×
- [ ] 使用不同模型時套用該模型自身單價
- [ ] Run 紀錄依 experiment 與 arm 分層落地並進版控，原始 usage 不做預先彙總
- [ ] 計價邏輯有測試覆蓋，且測試不需要網路或付費呼叫
- [ ] 自建 harness 固定使用 5 分鐘 cache TTL
