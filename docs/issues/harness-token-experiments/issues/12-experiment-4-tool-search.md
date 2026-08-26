# 12: Experiment 4a–4b — 動態 tool 選擇

**What to build:** 配置一個暴露遠多於所需 tool 的任務，比較全部 tool 直接暴露與 tool search 搭配延遲載入。兩個 harness 皆執行。

**Blocked by:** 04, 05, 07

**Status:** ready-for-agent

- [ ] 任務暴露的 tool 數量遠多於實際需要，實際只需其中少數
- [ ] 4a、4b 各三次 run，兩個 harness 分別執行
- [ ] 報告 tool 定義本身佔用的 token，以及它對 cache write 的影響
- [ ] 報告各 arm 的 pass/fail 次數，確認延遲載入未導致模型找不到需要的 tool
- [ ] 兩個 harness 的結果分開呈現
