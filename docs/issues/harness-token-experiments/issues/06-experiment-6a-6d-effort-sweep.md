# 06: Experiment 6a–6d — effort 掃描

**What to build:** 以四種 effort（low、medium、high、xhigh）各跑三次主任務，比較通過率與成本。這是第一個垂直切片的完成點，也是其餘所有 experiment 的比較基準：若單純調整 effort 就能省下可觀成本，後續複雜機制必須省得更多才值得投入。

**Blocked by:** 04, 05

**Status:** in-progress

- [x] 6a、6b、6c、6d 各三次 run，共十二次
- [x] 每個 arm 報告美元成本的中位數與最大最小值
- [x] Thinking token 單獨列出，可觀察 effort 與推理成本的關係
- [x] 報告各 arm 的 pass/fail 次數
- [ ] 此切片不引入任何 seam 抽象

## Comments

**狀態為 in-progress：實際掃描需要 12 次付費呼叫的任務，未執行過。**

`FixerAgent` 新增 `effort` 欄位，透過 `output_config={"effort": ...}` 送出（SDK 已驗證接受
`Literal["low","medium","high","xhigh","max"]`）。`run_arm` 因此重構：原本自己組裝 agent，
現在改吃一個 `agent_for(run) -> FixerAgent` 工廠，讓呼叫端決定 effort、style、model 如何隨
arm 變化，而不必替每個新變因加一個參數。

已驗證（無需呼叫）：`ARMS` 涵蓋 low 到 xhigh 四級（6e/6f 的流程拆解屬於 ticket 14，不在此列）；
每次 run 拿到獨立的 fixture 副本，第二次不會接手第一次留下的變動。

thinking token 的觀察本來就在 `RunRecord.tokens.thinking` 裡（ticket 01），這裡不需要額外
機制；掃描跑完後直接讀取即可。

`_system_blocks` 額外開了一個測試用的存取點（`system_blocks_for_test`），讓 output style
的附加行為可以在不呼叫 API 的情況下驗證：frozen 的任務 prompt 不被改寫，style 只附加在後面
——因為改寫 frozen block 會讓 cache prefix 失效。
