# hakka-vibe

一個可重複使用的 Python agent harness，以及一組用來量測不同 harness 設計省下多少 token 成本的實驗。

## Language

### Agent 架構

**Harness**:
承載 agent 執行的那層程式：組裝 prompt、驅動迴圈、收集 usage。
_Avoid_: framework, runtime, engine

**Agent**:
一個 Python class，其 method 是它的 capability，其 field 是它的 typed state。
_Avoid_: bot, assistant, worker

**Capability**:
Agent class 上的一個 method。可能是 deterministic（有真正的 body）或 agentic（交給模型）。
_Avoid_: function, action, skill（skill 專指 Claude Code 的 skill）

**Skill**:
`.claude/skills/` 底下的 Claude Code skill。永遠不用來指 agent 的 method。
_Avoid_: 用 skill 稱呼 capability

**Seam**:
可以替換行為而不必改動該處的位置，介面所在之處（沿用 `codebase-design` 的定義）。Harness 中每個可替換的部位都是 seam。
_Avoid_: pluggable point, extension point, boundary, hook

### 資料與記憶

**DataRef**:
指向 process 內大量資料的薄引用，生命週期只有一次任務。模型看到的是預覽，不是內容。
_Avoid_: 單獨使用 memory 一詞指涉它

**MemoryStore**:
跨 session 的知識存放。尚未實作。
_Avoid_: 單獨使用 memory 一詞指涉它

**Memory**:
未經修飾時語意不明，不要單獨使用。一律指明 `DataRef` 或 `MemoryStore`。

**Pass by reference**:
資料留在執行環境、只有預覽進入 prompt。判準是「這份資料的完整內容有沒有變成 prompt 的字元」，與用什麼查詢引擎無關。
_Avoid_: streaming, lazy loading

**Pass by value**:
資料的完整內容成為 prompt 的字元。用 SQL 只取 10 列然後塞進 prompt，仍然是 pass by value。

**Context**:
送進模型的那段內容。不指 `CONTEXT.md`（那是詞彙表），也不指 DDD 的 bounded context。
_Avoid_: window, history（history 專指對話紀錄那一段）

### 實驗

**Experiment**:
針對單一變因的一組比較，編號 1 到 6。
_Avoid_: test（test 專指 pytest 的測試）

**Arm**:
一個 experiment 底下的一個受測條件。
_Avoid_: variant, condition, case

**Run**:
一個 arm 執行一次，產出一份完整 usage 紀錄。每個 arm 跑三次。
_Avoid_: trial, iteration（iteration 是 usage 物件裡的既有欄位）

**Fixture**:
被測 agent 要操作的那份凍結程式碼：一個生成的 Python repo，內含機械注入的 bug。
_Avoid_: sample, testbed, target repo

**Calibration gate**:
Fixture 的驗收條件：baseline 執行少於八輪即視為過於簡單，須加深後重新生成。
_Avoid_: threshold, difficulty check

### 成本

**Cost model**:
把各類 token 依單價比例換算成美元的公式。實驗結論一律以美元表述。
_Avoid_: token count, usage（usage 專指 API 回傳的原始物件）

**Cache write**:
寫入快取的 input token，依 TTL 分 1 小時與 5 分鐘兩種，單價不同。
_Avoid_: cache creation（欄位名是 `cache_creation_input_tokens`，但敘述時用 cache write）

**Cache read**:
命中快取的 input token。

**Thinking token**:
模型推理產生的 token，計為 output，單價與一般 output 相同。
_Avoid_: reasoning token
