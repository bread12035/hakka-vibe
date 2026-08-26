# 06: Experiment 6a–6d — effort 掃描

**What to build:** 以四種 effort（low、medium、high、xhigh）各跑三次主任務，比較通過率與成本。這是第一個垂直切片的完成點，也是其餘所有 experiment 的比較基準：若單純調整 effort 就能省下可觀成本，後續複雜機制必須省得更多才值得投入。

**Blocked by:** 04, 05

**Status:** ready-for-agent

- [ ] 6a、6b、6c、6d 各三次 run，共十二次
- [ ] 每個 arm 報告美元成本的中位數與最大最小值
- [ ] Thinking token 單獨列出，可觀察 effort 與推理成本的關係
- [ ] 報告各 arm 的 pass/fail 次數
- [ ] 此切片不引入任何 seam 抽象
