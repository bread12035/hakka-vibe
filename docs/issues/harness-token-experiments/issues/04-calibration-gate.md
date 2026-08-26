# 04: Calibration gate

**What to build:** 量測 fixture 的 baseline 執行輪數，作為 fixture 的驗收條件。少於八輪即判定過於簡單，須加深模組層數重新生成。這讓「素材夠不夠難」從假設變成可驗收的事實。

**Blocked by:** 03

**Status:** ready-for-agent

- [ ] 能報告一趟 baseline 執行的輪數
- [ ] 少於八輪時明確判定 fixture 不合格
- [ ] 判定結果與當次 run 紀錄一併留存，日後可追溯當時使用的是哪一版 fixture
- [ ] 重新生成後可再次執行判定
