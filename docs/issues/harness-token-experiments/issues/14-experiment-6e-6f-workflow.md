# 14: Experiment 6e–6f — 先規劃再執行

**What to build:** 建立「主 agent 先產出計畫、再逐步執行」的流程，比較它與單一 agent 直接完成任務的 thinking 成本差異，並測試低 effort 搭配明確計畫能否取得與高 effort 相近的通過率。

**Blocked by:** 04, 05

**Status:** in-progress

- [ ] 6e、6f 各三次 run
- [ ] 與 06 的 effort 掃描結果對照，判斷流程拆解是否換到等值的節省
- [x] Thinking token 單獨列出，這是本 experiment 的主要觀察對象
- [ ] 報告各 arm 的 pass/fail 次數，6f 需確認低 effort 未損及通過率
- [ ] 若結果顯示拆解並未較省，該結果視為有效結論而非實驗失敗

## Comments

**狀態為 in-progress：6 次付費呼叫（含每次 run 額外的一次規劃呼叫）未執行。**

`FixerAgent` 新增 `plan()`：修復迴圈開始前先呼叫一次，用同一個 arm 的 effort 產生
3-6 步的規劃文字，計入 `self.calls`——假設要驗證的是「規劃一次之後，後續每輪能不能
想得更淺」，不是「規劃本身該便宜」，所以規劃呼叫刻意套用跟其餘呼叫相同的 effort。

把「初始 task message 怎麼組出來」抽成純函數 `_assemble_task(plan=...)`，跟取得 plan
的方式（一定要呼叫 API）分開。這樣「plan 折進第一則訊息的位置對不對、跟 briefing 共存
時順序對不對」可以在不呼叫 API 的情況下測試——`plan` 折在 `briefing` 之後，測試逐一
確認兩段文字都在、且順序正確。

6e／6f 唯一的差異是 effort（high／low），比較基準是 ticket 06 的 6a／6c，不在本票內
重建：如果 6f（低 effort + 有計畫）的通過率跟成本接近 6c（高 effort、無計畫），代表
規劃這道機制換到的東西划算；如果沒有，也是有效結論。

開發時發現一個會弄髒 repo 的問題：`fresh_copy_of` 會在 fixture 的**父目錄**寫入隱藏
資料夾（`fixtures/.pipeline-6e-1` 之類）。原本我在測試裡直接把 `fixtures/pipeline`
當 `fixture` 傳給 `build_agent`，導致這些隱藏資料夾寫進真正的 repo 目錄而非 `tmp_path`。
已修正測試（改成先複製到 `tmp_path` 再操作）並在 `.gitignore` 補上這個樣式，避免下次
再犯。
