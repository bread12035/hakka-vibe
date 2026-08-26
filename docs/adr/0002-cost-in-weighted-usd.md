# 實驗成本以加權美元衡量，不以 token 總數

四類 token 的單價相差最多五十倍（cache read 0.1×、input 1×、cache write 1.25× 或 2×、output 5×），所以「省了多少 token」這個問題沒有唯一答案。所有 experiment 的結論一律換算成美元表述，token 細項保留作為診斷資料。

## Consequences

- 若某段內容原本就以 cache read 計費，把它移出 context 只省下 0.1×。用 token 總數看會**高估十倍**。
- Cache write 必須依 TTL 分開計算：自建 harness 固定 5 分鐘（1.25×），Claude Code 固定 1 小時（2×，不可調）。兩個 harness 的百分比不可放在同一張表比較。
- Experiment 3 的 Arm B（handoff 壓縮）**必須把主 agent 產生壓縮摘要所花的 output token 計入該 arm**。壓縮省下的是 subagent 的 input token（Sonnet 5，$2/MTok），付出的是主 agent 的 output token（Opus 5，$25/MTok）。不計入的話 Arm B 必然勝出，而那個勝出是假的。
