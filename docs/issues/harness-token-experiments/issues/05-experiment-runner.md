# 05: Experiment runner

**What to build:** 依 arm 設定執行 run，每個 arm 跑三次，輸出中位數與最大最小值。結果依 experiment 與 arm 分層落地。這是後續每一個 experiment 共用的執行入口。

**Blocked by:** 03

**Status:** in-progress

- [ ] 能依 arm 設定執行，每個 arm 三次 run
- [x] 報告中位數，並一併回報最大與最小值
- [ ] 每次 run 各自產出一份獨立紀錄，原始 usage 完整保留
- [x] 此入口僅有一個 smoke test，以最小 fixture 與最低 effort 執行一次，確認整條管線連通
- [x] 不在此入口做單元測試，因每次執行都需付費呼叫

## Comments

**狀態為 in-progress：執行迴圈需憑證，未驗證。** 統計部分（中位數、最大最小、通過數）
是純函數且已完整測試。

`summarise` 在收到非三次 run 時直接報錯而非照算——兩次 run 的「中位數」其實是平均數，
用同一個名字回報會誤導。

通過數與成本一起回報，因為單看成本會獎勵錯的東西：**最便宜的 arm 是立刻放棄的那個**。
`spread`（最大減最小）是獨立的結果，不是附註——runs 之間差 40% 的 arm 撐不起「省了 20%」
這種說法。

`run_arm` 每次 run 都要一份全新的 fixture 副本，否則第二次 run 會接手第一次留下的狀態。
