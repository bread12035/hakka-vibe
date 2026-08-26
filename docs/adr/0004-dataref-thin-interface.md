# `DataRef` 維持薄介面

`DataRef` 只提供 `preview()` 與取得底層物件的途徑，不提供 `query()`、`describe()`、`sample()` 這類方法。需要什麼資料，由模型自己寫 code 取用。

## Considered Options

- **厚介面（包一層 query/describe/sample）**：否決。每次查詢都成為一次 tool call，也就是一次 round trip，這正是 pass by reference 想避免的成本結構；而且介面複雜度逼近實作複雜度，是 `codebase-design` 定義的 shallow module，通不過 deletion test。

## Consequences

模型必須有能力執行自己寫的 code，harness 因此需要一個執行環境。這是 experiment 2 本來就要建的東西，不是額外成本。
