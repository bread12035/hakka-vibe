# 03: 最小 agent 完成主任務

**What to build:** 一個 agent 讀取 fixture、探索程式碼、修改檔案，直到 pytest 轉綠或放棄。整趟過程的 usage 被記錄成 run 紀錄。這是第一次真實的 run，也是 pass/fail 閘門第一次生效。

**Blocked by:** 01, 02

**Status:** in-progress

- [x] Agent 結構依 ADR-0001：一個 agent 一個 class，state 放 typed field，model-facing 邊界型別化
- [x] Python 檔中不含任何 prompt 字串常數
- [x] Pass/fail 完全取自 fixture 自身 pytest 的 exit code，無人工判斷
- [ ] 一趟完整任務的 usage 被記錄成 run 紀錄，格式與 01 相同
- [x] Agent 本身不另設 seam，其正確性由 pytest exit code 驗證
- [ ] 能在 agent 無法收斂時終止並記為 fail，不會無限迴圈

## Comments

**狀態為 in-progress 而非 done：兩條驗收條件無法在本環境驗證。** 容器無 `ANTHROPIC_API_KEY`
亦無 `ant` CLI，agent 迴圈的全部行為都在 API 呼叫的另一端。程式碼已寫完、mypy strict 通過，
但「它真的會動」未經證實。

已驗證：

- **Pass/fail 閘門**對著真實的 `fixtures/pipeline` 測過：目前判為 fail，把注入的那一行還原後
  判為 pass。閘門讀錯 exit code 會讓「修好了」與「什麼都沒做」記成同一件事，屬於與 cost model
  同級的靜默錯誤。
- **`.py` 中無 prompt 字串**由測試守住。

未驗證（需憑證）：一趟完整任務的 usage 累積、輪數上限的終止行為。`tests/test_call_smoke.py`
已寫好對應的 smoke test，有憑證時跑一次 `pytest` 即可補上。

實作中浮現的設計變更：`RunRecord` 原本只裝一次呼叫的 usage（ticket 01 的範圍就是一次呼叫），
但一趟任務是多次呼叫。已改為 `calls: tuple[...]`，逐次保留、讀取時加總——彙總後存會失去
「成本花在任務的哪個階段」這個資訊。ticket 01 的測試已同步更新。

Tool schema 由方法簽章推導而非手寫 JSON，依 `nooa-design`；手寫的副本會靜默地與程式碼失去對應。

Prompt registry 目前是最小形式（`prompts/<key>.md` + `str.format`），未做 YAML、版本化、
CD 交付與 CI 契約測試——那些依 spec 不在本切片範圍。但「`.py` 中不含 prompt 字串」這條
從第一天生效，因為事後抽離的成本很高。
