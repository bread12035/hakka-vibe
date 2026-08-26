# 10: Experiment 2d–2e — Claude Code 上的 pass by reference

**What to build:** 在 Claude Code 上比較兩種資料傳遞方式：資料置於 sandbox 由 pandas 取用，對照資料以文字全量塞入。沿用 09 建立的資料分析任務，驗證同樣的原理在既有工具上是否成立。

**Blocked by:** 07, 09

**Status:** ready-for-agent

- [ ] 沿用 09 的資料分析任務與判準
- [ ] 2d、2e 各三次 run
- [ ] Run 紀錄透過 07 的 adapter 產出
- [ ] 2e 需刻意將資料以文字全量置入，而非依賴 Claude Code 的預設行為
- [ ] 結果與 2a–2c 分開呈現，不與自建 harness 的百分比合併
