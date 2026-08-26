# 07: Claude Code usage adapter

**What to build:** 解析 Claude Code 的 session transcript，產出與自建 harness 同型的 run 紀錄。Claude Code 的 transcript 已含每次呼叫的完整 usage，包括 thinking token 與依 TTL 分流的 cache write，因此不需要額外的遙測設定。

**Blocked by:** 01

**Status:** done

- [x] 從 session transcript 產出 run 紀錄，型別與自建 harness 相同
- [x] 保留逐輪明細（`iterations`）：此欄位僅存在於 Claude Code 的 transcript，API 回應沒有，故由本票承接
- [x] 這是 RunRecord 建構的第二個 adapter，使該 seam 具備兩個真實 adapter
- [x] 套用 1 小時 TTL 的 cache write 單價，因 Claude Code 的 TTL 不可設定
- [x] 解析邏輯有測試覆蓋，測試不需要網路
- [x] 報告輸出時標明兩個 harness 的百分比不可跨比

## Comments

**這張票逼出一個修正，影響 01、03、05、06。** 用真實 transcript 開發時發現：一個 Claude
Code session 可以在對話中途切換模型（這個 session 自己的 transcript 就同時有
`claude-opus-5` 與 `claude-sonnet-5`）。`RunRecord` 原本用單一 `model` 對整趟 run 的加總
token 計價——混模型的 run 會用錯的單價算到部分呼叫。已改為 `Call(model, usage)`，每次呼叫
各自計價再加總，`RunRecord.model` 保留為報告用的名義標籤，不再是計價輸入。獨立 commit
處理，因為既有的每個呼叫端在混模型 transcript 出現的當下就已暴露在這個錯誤裡。

已用這個 session 自己的真實 transcript 做完整性檢查（非測試，手動驗證）：418 次呼叫、
兩種模型正確分開，計算出的成本量級合理。這是目前唯一被真實資料驗證過的元件。

非 usage 的 transcript 行（`user`、`queue-operation` 等）明確被跳過而非誤讀為零成本呼叫——
這與 01 的「缺欄位報錯而非計 0」是同一類防禦，只是方向相反：這裡是「不屬於呼叫的行不能被
當成呼叫」。

Claude Code 固定用 1 小時 TTL 寫入 cache，是它自身行為、非本專案可設定，因此本 adapter
產出的結果永遠不與自建 harness 的百分比放在同一張表比較（依 spec）。
