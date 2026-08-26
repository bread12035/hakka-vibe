# 13: Experiment 3a–3c — subagent 架構

**What to build:** 建立 subagent 的生命週期與 context 傳遞機制，比較三種架構：傳遞完整對話紀錄且每次全新建立、傳遞壓縮摘要且每次全新建立、以及持續存活只傳增量。Subagent 一律使用較便宜的模型。

**Blocked by:** 04, 05

**Status:** in-progress

- [ ] 3a、3b、3c 各三次 run
- [x] 3b 產生壓縮摘要所耗的主 agent output token 計入 3b 自身，依 ADR-0002
- [x] 3c 首次傳遞內容與 3a 相同，使兩者成為單變因對照
- [ ] 分析時將模型單價變因與架構變因分離，報告需能回答「省下來的是模型單價還是架構設計」
- [x] 先計算 3b 的損益平衡點：壓縮需省下多少 subagent input token，才抵得過主 agent 的壓縮 output token
- [ ] 報告各 arm 的 pass/fail 次數，確認壓縮未導致 subagent 資訊不足

## Comments

**狀態為 in-progress：9 次付費呼叫未執行，`FixerAgent` 的完整修復迴圈也在這裡被觸發，
一次 run 因此比其他 experiment 更貴。**

架構：主 agent（Opus）在動手修 fixture 之前，先對一個較便宜模型（Sonnet）的 subagent
委派兩題調查（各查一個非入口模組），把調查結果折進 `FixerAgent` 新增的 `briefing` 欄位，
再讓 `FixerAgent` 走它原本的修復迴圈。三個 arm 只在「委派時傳什麼 context、subagent
活多久」上不同，調查題目、orchestrator 模型、修復迴圈完全一致——這樣結果的差異只能來自
被測的變因本身。

`context_for_call` 是三個 arm 唯一分岔的地方，做成純函數並完整測過（不需要呼叫）：

- 3a：每次委派都是全新 subagent，因此**每次都要重送完整歷史**——它沒有自己的記憶。
- 3b：只送 orchestrator 已經壓縮過的摘要，不連原始歷史一起送。壓縮呼叫的成本明確
  記在 3b 自己頭上（依 ADR-0002），不是記在 subagent 的呼叫裡——`_delegate_investigation`
  把 `compress()` 回傳的 `Call`併入 `spent` 清單，最後跟 `FixerAgent.calls` 一起塞進
  同一份 `RunRecord`。
- 3c：一個 subagent 物件在整個 run 裡只建立一次，**只有第一次委派送完整歷史，之後只送
  新增的部分**——因為它自己的對話紀錄已經留著其餘的。3c 的第一次委派內容故意設計成與 3a
  完全相同，讓兩者成為乾淨的單變因對照，藉此分離出「subagent 持續存活」單獨值多少。

`Subagent.ask()` 本身也驗證過（無需呼叫）：`prompts/subagent.system.md` 存在、
只有一個 `read_file` 能力（不能改檔案，只能調查）。

新增 `briefing` 欄位到 `FixerAgent`：折進第一則 task message，已用不呼叫 API 的測試
驗證真的接進去了（而不是死欄位）。

損益平衡點在票的驗收條件裡要求先算，但實際數字要等真的跑過 3b 才有——這裡先確保
「壓縮成本記在哪個 arm」這件事在程式碼層面是對的，數字留給執行後補。
