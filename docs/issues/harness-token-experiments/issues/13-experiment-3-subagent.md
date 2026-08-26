# 13: Experiment 3a–3c — subagent 架構

**What to build:** 建立 subagent 的生命週期與 context 傳遞機制，比較三種架構：傳遞完整對話紀錄且每次全新建立、傳遞壓縮摘要且每次全新建立、以及持續存活只傳增量。Subagent 一律使用較便宜的模型。

**Blocked by:** 04, 05

**Status:** ready-for-agent

- [ ] 3a、3b、3c 各三次 run
- [ ] 3b 產生壓縮摘要所耗的主 agent output token 計入 3b 自身，依 ADR-0002
- [ ] 3c 首次傳遞內容與 3a 相同，使兩者成為單變因對照
- [ ] 分析時將模型單價變因與架構變因分離，報告需能回答「省下來的是模型單價還是架構設計」
- [ ] 先計算 3b 的損益平衡點：壓縮需省下多少 subagent input token，才抵得過主 agent 的壓縮 output token
- [ ] 報告各 arm 的 pass/fail 次數，確認壓縮未導致 subagent 資訊不足
