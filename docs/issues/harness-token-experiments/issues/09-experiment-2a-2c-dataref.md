# 09: Experiment 2a–2c — pass by reference 與 DataRef

**What to build:** 建立 `DataRef` 與模型可執行自寫程式碼的環境，配置資料分析任務，比較三種資料傳遞方式：資料全文進入 context、以 `DataRef` 包裝 in-process 資料、以 `DataRef` 包裝 SQLite。判準為答案數值正確。

**Blocked by:** 04, 05

**Status:** ready-for-agent

- [ ] `DataRef` 依 ADR-0004 維持薄介面：提供預覽與取得底層物件的途徑，不提供查詢方法
- [ ] 模型能執行自己寫的程式碼以取用資料
- [ ] 資料分析任務的 pass/fail 為答案數值是否正確
- [ ] 2a、2b、2c 各三次 run
- [ ] 報告時區分 pass by value 與 pass by reference：判準是資料的完整內容有沒有變成 prompt 的字元，與查詢引擎無關
- [ ] 觀察 2a 是否觸發 context 溢位與 compact，並記錄其對 cache 的影響
