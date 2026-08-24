# hakka-vibe — Agent 工作流程

這個 repo 收錄了 [mattpocock/skills](https://github.com/mattpocock/skills) 的 skills，放在 `.claude/skills/`。
Code agent 在對應階段**請主動使用**下列 skills，不要憑感覺直接開工。

## 四個階段

### 1. 釐清需求 → `grill-me` / `grill-with-docs`

需求還模糊、只有一句話的想法、或計畫有沒想清楚的分支時，先被逼問過一輪再說。

- `/grill-me`：純訪談。一輪一輪問，每題附上建議答案，等使用者回答完才問下一輪。
- `/grill-with-docs`：訪談的同時把結論寫成文件（`CONTEXT.md` 詞彙表與 `docs/adr/` 的 ADR）。碰到會影響長期架構的決策，用這個。

訪談沒收斂前，不要進入下一階段。

### 2. 需求轉任務 → `to-spec` → `to-tickets`

- `/to-spec`：把目前對話（含 grilling 的結論）整理成 spec，發到 issue tracker。這個階段**不再訪談**，只做整理。
- `/to-tickets`：把 spec 或計畫拆成 tracer-bullet 的垂直切片，每張票標明被哪些票 blocking。

兩者順序是 spec 先、tickets 後；已經有 spec 的話可以直接跑 `/to-tickets`。

### 3. 寫 code → `implement` + `tdd`

- `/implement`：依 spec 或票實作。它會在事先講好的 seam 上用 TDD、定期跑 typecheck 與單一測試檔、最後跑一次完整測試，然後叫 `/code-review`，最後 commit。
- `/tdd`：red-green-refactor 的準則本體。什麼算好測試、seam 放哪、哪些是反模式（測 private、mock 內部協作者、從側門查資料庫驗證）。

**seam 要先跟使用者確認過才寫測試**——這是 `tdd` 的硬規則，不要跳過。

### 4. 定期審核架構 → `code-review` / `improve-codebase-architecture`

- `/code-review`：審查從某個固定點（commit / branch / tag / merge-base）到 `HEAD` 的 diff，兩條軸線並行跑子代理：Standards（是否符合本 repo 規範）與 Spec（是否忠實實作原始 issue）。每次要合併前跑。
- `/improve-codebase-architecture`：週期性做。掃 codebase 找 shallow module、出 HTML 報告，挑一項後接著 grilling 深入。

## 前置設定

`/setup-matt-pocock-skills` 已經跑過，設定寫在 `docs/agents/`，見下方「Agent skills」。要換 issue tracker（例如改用 GitHub issues）才需要重跑。

各 skill 的來源、版本與更新方式見 `.claude/skills/README.md`。

## Agent skills

### Issue tracker

Issues and specs live as markdown files under `docs/issues/`, committed to the repo. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context: `CONTEXT.md` at the root, ADRs in `docs/adr/`. See `docs/agents/domain.md`.
