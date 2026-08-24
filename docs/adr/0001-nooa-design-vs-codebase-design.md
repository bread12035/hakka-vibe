---
status: accepted
---

# `nooa-design` 與 `codebase-design` 的分工

本 repo 同時收錄了兩個會在設計階段觸發的 skill：`nooa-design`（agent 架構的結構模板）與 `codebase-design`（deep module 的評價標準，被 `tdd` 與 `improve-codebase-architecture` 當作共用詞彙）。寫 agent code 時兩者會同時被叫起來。我們**採取分層分工**：結構問題依 `nooa-design`，設計品質的判準依 `codebase-design`。

## 三條規則

1. **結構聽 `nooa-design`**：agent 的 class 邊界（一個 agent 一個 class）、state 放 typed field、prompt 走外部 registry、model-facing 邊界一律型別化。
2. **判準聽 `codebase-design`**：「這個方法該不該存在」「介面能不能再窄」「seam 放哪」依 deep module 那套。**agent class 不豁免 deletion test。**
3. **測試斷言**：`nooa-design` capability 5 要求對 typed field 直接斷言。這類 field 必須同時宣告為介面的一部分（`codebase-design` 對 interface 的定義是「everything a caller must know to use the module correctly」，公開且文件化的 field 符合）。非公開的內部記帳欄位不得被測試斷言 —— 那是 `tdd` 明列的 side channel 反模式。

## 為什麼是分層，不是領域切分

兩者其實不在同一層。`codebase-design` 是評價標準且明確 scale-agnostic；`nooa-design` 是單一領域的結構模板。關鍵事實：**`nooa-design` 全文對「介面該有幾個方法」沒有任何立場**（`SKILL.md` 與三份 references 皆無），而 `codebase-design` 的核心主張正是「Can I reduce the number of methods?」。這不是對撞，是一邊有主張、一邊留白，可以直接互補。

真正的張力只有三處，即上面三條規則對應的：介面寬度（capability 3 的「expose methods on `self`」隱含往寬推）、測試斷言的位置、以及「one adapter = hypothetical seam」對上 nooa 第一天就要求的依賴注入。第三點自然解消：測試替身（fake `OrderDB`）就是第二個 adapter，seam 的成立條件本來就滿足。

詞彙上沒有衝突：`codebase-design` 禁用的 component / service / API / boundary，`nooa-design` 都沒用到（唯一擦邊是 capability 6 標題的 "harness APIs"，改稱 harness interface 即可）。

## Considered Options

- **領域切分（agent code 歸 nooa，其餘歸 codebase-design）**：規則最簡單，但會把 depth 判準整個排除在 agent code 之外。agent class 正是最容易長成巨型介面的地方（capability 3 持續鼓勵 expose 更多方法），恰恰最需要 deletion test。否決。
- **優先序（nooa 優先，codebase-design 當 tiebreak）**：看似折衷，實則退化成領域切分 —— 因為 nooa 對介面寬度沒立場，「衝突」永不觸發，codebase-design 永遠輪不到。否決。

## Consequences

- 本 ADR 只在專案真的出現 agent code 時才有作用。決策當下 repo 尚無任何 code，規則未經實際驗證。
- `nooa-design` 的範例與機制全為 Python（`@agentic`、Pydantic、`...` 方法體、runtime 型別驗證與 auto-retry）。若本專案採用其他語言，六個 capability 的觀念可移植，但 capability 1 與 4 的實作細節需重新設計，屆時應補一份 ADR。
