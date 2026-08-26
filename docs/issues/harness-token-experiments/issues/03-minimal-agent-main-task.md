# 03: 最小 agent 完成主任務

**What to build:** 一個 agent 讀取 fixture、探索程式碼、修改檔案，直到 pytest 轉綠或放棄。整趟過程的 usage 被記錄成 run 紀錄。這是第一次真實的 run，也是 pass/fail 閘門第一次生效。

**Blocked by:** 01, 02

**Status:** ready-for-agent

- [ ] Agent 結構依 ADR-0001：一個 agent 一個 class，state 放 typed field，model-facing 邊界型別化
- [ ] Python 檔中不含任何 prompt 字串常數
- [ ] Pass/fail 完全取自 fixture 自身 pytest 的 exit code，無人工判斷
- [ ] 一趟完整任務的 usage 被記錄成 run 紀錄，格式與 01 相同
- [ ] Agent 本身不另設 seam，其正確性由 pytest exit code 驗證
- [ ] 能在 agent 無法收斂時終止並記為 fail，不會無限迴圈
