# 09: Experiment 2a–2c — pass by reference 與 DataRef

**What to build:** 建立 `DataRef` 與模型可執行自寫程式碼的環境，配置資料分析任務，比較三種資料傳遞方式：資料全文進入 context、以 `DataRef` 包裝 in-process 資料、以 `DataRef` 包裝 SQLite。判準為答案數值正確。

**Blocked by:** 04, 05

**Status:** in-progress

- [x] `DataRef` 依 ADR-0004 維持薄介面：提供預覽與取得底層物件的途徑，不提供查詢方法
- [x] 模型能執行自己寫的程式碼以取用資料
- [x] 資料分析任務的 pass/fail 為答案數值是否正確
- [ ] 2a、2b、2c 各三次 run
- [x] 報告時區分 pass by value 與 pass by reference：判準是資料的完整內容有沒有變成 prompt 的字元，與查詢引擎無關
- [ ] 觀察 2a 是否觸發 context 溢位與 compact，並記錄其對 cache 的影響

## Comments

**狀態為 in-progress：9 次付費呼叫未執行。**

新增 `AnalystAgent`，與 `FixerAgent` 是分開的 class——兩者是不同種類的 agent（一個對著測試
套件改檔案，一個對資料集寫程式回答問題），符合 ADR-0001：「一個 agent 一個 class」指的是
一種 agent 一個 class，不是整個專案只能有一個 agent class。

`sandbox.execute_python` 的 namespace **跨輪次持續存活**（同一個 agent 執行個體內），
這是 pass by reference 真正省錢的機制：`patterns.md` 的 "df stays live" ——上一輪算出的
中繼結果不必重新查詢或序列化。（第一版測試方向寫反了，以為每次呼叫該重置 namespace，
與機制的本意矛盾，已修正。）

已驗證（無需呼叫）：

- `DataRef.preview()` 對 10 萬列的 DataFrame 回傳的描述不含任何一列資料，且長度有上限；
  對 SQLite 連線只列出資料表名稱，不含任何一列資料。
- 正解 `top_customer_by_total` 用**跟被測方法不同的計算路徑**驗證（純 Python 迴圈加總對照
  pandas groupby），避免測試套套邏輯（tautology）。
- 三個 arm 的差異：2a 把整份資料集的每一列 amount 都能在 task context 的純文字裡找到
  （名副其實的 pass by value）；2b、2c 的 task context 完全不含任何一列的 amount 值，
  只有變數名稱與型別描述。
- 答案比對容許一分錢的四捨五入誤差，但客戶編號必須完全相符。

執行 2a-2c 不需要像 02/03 那樣為每個 run 複製一份 fixture——資料集是唯讀的分析對象，
每次 run 各自的 `AnalystAgent` 有獨立的 `namespace`，不會互相污染。

附帶修正：`FixerAgent` 與 `AnalystAgent` 原本 tool_result 內容用一般 dict 建構，
`AnalystAgent` 先改用型別化的 `ToolResultBlockParam`，隨後回頭讓 `FixerAgent` 保持一致，
避免同一個 pattern 一邊型別化、一邊沒有。
