# 04: Calibration gate

**What to build:** 量測 fixture 的 baseline 執行輪數，作為 fixture 的驗收條件。少於八輪即判定過於簡單，須加深模組層數重新生成。這讓「素材夠不夠難」從假設變成可驗收的事實。

**Blocked by:** 03

**Status:** done

- [x] 能報告一趟 baseline 執行的輪數
- [x] 少於八輪時明確判定 fixture 不合格
- [x] 判定結果與當次 run 紀錄一併留存，日後可追溯當時使用的是哪一版 fixture
- [x] 重新生成後可再次執行判定

## Comments

閘門是對 `RunRecord` 的純函數：一次 run 的輪數就是它發出的呼叫數，不需要額外的量測機制。
邊界為 inclusive（八輪通過、七輪不通過），已明確測試——這裡的 off-by-one 會靜默改變哪些
fixture 被允許使用。

`RunRecord` 新增 `fixture` 欄位，存放 fixture 內容的 fingerprint。沒有它，判定結果會脫離
它的對象：fixture 加深重生成之後，舊紀錄與新紀錄無法區分。

尚未執行真實 baseline（需憑證），因此 `fixtures/pipeline` 的 `depth=8` 仍是未經驗證的猜測。
