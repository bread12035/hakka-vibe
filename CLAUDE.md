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

新增檔案放進 `src/hakka_vibe/` 的哪個分類，見下方「新檔案放哪裡」。

### 4. 定期審核架構 → `code-review` / `improve-codebase-architecture`

- `/code-review`：審查從某個固定點（commit / branch / tag / merge-base）到 `HEAD` 的 diff，兩條軸線並行跑子代理：Standards（是否符合本 repo 規範）與 Spec（是否忠實實作原始 issue）。每次要合併前跑。
- `/improve-codebase-architecture`：週期性做。掃 codebase 找 shallow module、出 HTML 報告，挑一項後接著 grilling 深入。

## 寫 agent code 時的優先序

`nooa-design` 與 `codebase-design` 會同時觸發。分工是**分層的**：

1. **結構聽 `nooa-design`** —— class 邊界、state 放 typed field、prompt 走外部 registry、model-facing 邊界型別化。
2. **判準聽 `codebase-design`** —— 方法該不該存在、介面能不能再窄、seam 放哪。agent class 不豁免 deletion test。
3. **`nooa-design` 要斷言的 typed field，必須同時是介面的一部分**（公開且文件化）。內部記帳欄位不得被測試斷言 —— 那是 `tdd` 的 side channel 反模式。

理由與被否決的方案見 [ADR-0001](docs/adr/0001-nooa-design-vs-codebase-design.md)。

## 新檔案放哪裡：`src/hakka_vibe/` 的分類

`src/hakka_vibe/` 依角色分四個子套件，不是扁平目錄。寫新模組時（`/implement` 執行任務時一併參考），先按這張表決定放哪裡：

| 子套件 | 放什麼 | 判準 |
| --- | --- | --- |
| `agents/` | agent class，一個 class 一個檔 | `nooa-design` 規定：one agent, one class, one file |
| `seams/` | 至少一組 experiment 會拿來當變因替換的模組 | 這個模組換掉，其他地方的程式碼不用跟著改 |
| `measurement/` | usage 怎麼來、怎麼記、怎麼算成美元、怎麼彙總成報告 | 不特定屬於某一組 experiment 的量測管線 |
| `fixture/` | 受測素材的生成與驗收 | 產生或驗收 `fixtures/` 底下那份凍結專案的程式碼 |
| 根目錄 | 上述四類都共用的基礎設施（如 `prompts.py`、`tool_schema.py`） | 不屬於任何單一分類，被全部分類引用 |
| `experiments/`（既有，不算這四類之一） | 六組 experiment 各自的 runner | 組裝 seam、跑 arm、寫 `results/` 的那一層 |

新增測試檔放進對應的 `tests/<分類>/`，跟 `src/` 鏡射；橫跨多個分類的整合測試（例如打真實 API 的 smoke test）留在 `tests/` 根目錄。

理由與被否決的方案見 [ADR-0006](docs/adr/0006-src-layout-by-role.md)。

## 前置設定

`/setup-matt-pocock-skills` 已經跑過，設定寫在 `docs/agents/`，見下方「Agent skills」。要換 issue tracker（例如改用 GitHub issues）才需要重跑。

各 skill 的來源、版本與更新方式見 `.claude/skills/README.md`。

## Agent skills

### Issue tracker

Issues and specs live as markdown files under `docs/issues/`, committed to the repo. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context: `CONTEXT.md` at the root, ADRs in `docs/adr/`. See `docs/agents/domain.md`.
