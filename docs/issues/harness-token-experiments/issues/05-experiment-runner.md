# 05: Experiment runner

**What to build:** 依 arm 設定執行 run，每個 arm 跑三次，輸出中位數與最大最小值。結果依 experiment 與 arm 分層落地。這是後續每一個 experiment 共用的執行入口。

**Blocked by:** 03

**Status:** ready-for-agent

- [ ] 能依 arm 設定執行，每個 arm 三次 run
- [ ] 報告中位數，並一併回報最大與最小值
- [ ] 每次 run 各自產出一份獨立紀錄，原始 usage 完整保留
- [ ] 此入口僅有一個 smoke test，以最小 fixture 與最低 effort 執行一次，確認整條管線連通
- [ ] 不在此入口做單元測試，因每次執行都需付費呼叫
