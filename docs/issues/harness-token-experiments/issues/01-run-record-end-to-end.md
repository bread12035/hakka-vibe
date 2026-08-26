# 01: 單次呼叫的成本記錄

**What to build:** 對模型發出一次呼叫，把回傳的 usage 換算成美元，寫成一份 run 紀錄落地。沒有 agent，沒有 fixture，只有「呼叫一次、算出錢、存起來」這條最薄的完整路徑。計價算術與紀錄格式在此定案，後續 72 次 run 全部沿用。

**Blocked by:** None (can start immediately)

**Status:** done

- [x] 一次呼叫的 usage 被完整保留：input、output、thinking token、cache read、依 TTL 分流的 cache write
- [x] Cost model 依 ADR-0002 換算：cache read 0.1×、input 1×、cache write 5m 1.25×、cache write 1h 2×、output 5×
- [x] 使用不同模型時套用該模型自身單價
- [x] Run 紀錄依 experiment 與 arm 分層落地並進版控，原始 usage 不做預先彙總
- [x] 計價邏輯有測試覆蓋，且測試不需要網路或付費呼叫
- [x] 自建 harness 固定使用 5 分鐘 cache TTL

## Comments

「逐輪明細」原列於本票，已移至 07。API 的 `Usage` 模型沒有 `iterations` 欄位（已驗證
`'iterations' in Usage.model_fields` 為 False）；該欄位只存在於 Claude Code 的 session
transcript，屬於 07 的 adapter。

Seam B 的 smoke test 已寫好但**在本次環境未執行**：容器內無 `ANTHROPIC_API_KEY` 亦無 `ant`
CLI，該測試會自動跳過。它是唯一需要付費呼叫的測試，其驗證的解析與計價邏輯在 Seam A 皆有覆蓋。
在有憑證的環境跑一次 `pytest` 即可補上這條驗證。

code-review findings 已處理：usage 欄位缺失改為報錯而非計 0、`max_tokens` 提高至 16000、
TTL 由散文改為程式碼層級的預設值、移除中介函式與重複的 import 路徑。Data Clumps
（experiment/arm/run）暫不抽型別，等第二個消費者出現。
