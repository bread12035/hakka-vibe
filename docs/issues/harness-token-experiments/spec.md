# Harness token cost experiments

Status: ready-for-agent

## Problem Statement

我想知道各種「省 token」的 harness 設計，在我自己的情境下究竟值不值得做。

市面上的宣稱彼此矛盾，而且幾乎都來自提出者本人。caveman output style 宣稱省 65%，JetBrains 實測是 8.5%。Devin Fusion 宣稱 35% 到 60%。NVIDIA 的 pass by reference 附了 SWE-bench 數字，但 `nooa-design` 自己就規定那些數字必須標為廠商數據、不得當成本專案的保證。這些手段的實作成本差距極大——換一個 output style 是改一個檔案，做 persistent subagent 是好幾週的工——但我沒有任何依據判斷該先投資哪一個。

同時我想建一個可重複使用的 agent harness。但我不知道該內建哪些機制，而這正是上面那些實驗要回答的問題。先蓋 harness 再量測，等於在拿到資料之前就把設計定死。

## Solution

建立一套量測基建與一個最小的 agent，用同一份凍結的 fixture 跑六組 experiment。每組 experiment 比較數個 arm，每個 arm 跑三次，結論一律以美元表述。

Harness 的能力由 experiment 逐一驅動長出來：每個 experiment 需要 harness 的哪個部位可替換，才在那裡開一個 seam。跑完六組之後，哪些機制真的省錢會有數據支撐，屆時再據以設計完整的 agent layer 與 MemoryStore。

第一個垂直切片刻意選最小的：量測基建 + 最小 agent + experiment 6 的 effort 掃描。effort 掃描只需要改一個 API 參數，harness 端零額外機制，卻能完整走過「執行任務 → 收集 usage → 換算成本 → 比較 arm → 存檔」的整條管線。它同時產出所有後續 experiment 的 baseline。

## User Stories

1. As a harness 研究者, I want 每一次 run 的完整 usage 被原封不動保存下來, so that 我日後想到新的分析角度時不必重跑上百次
2. As a harness 研究者, I want 成本以美元而非 token 總數表述, so that 我不會因為四類 token 單價相差五十倍而高估節省幅度
3. As a harness 研究者, I want 看到每一類 token 的細項用量, so that 我能診斷某個 arm 的成本究竟花在 cache write、input 還是 output
4. As a harness 研究者, I want cache write 依 1 小時與 5 分鐘 TTL 分開計算, so that 兩種 TTL 的單價差異不會被混在一起
5. As a harness 研究者, I want thinking token 單獨列出, so that 我能直接觀察 effort 設定與流程拆解對推理成本的影響
6. As a harness 研究者, I want 同一個 usage parser 同時服務自建 harness 與 Claude Code, so that 我不必維護兩套量測程式
7. As a harness 研究者, I want 每個 arm 跑三次並回報中位數與最大最小值, so that 我能判斷 arm 之間的差異是真的還是雜訊
8. As a harness 研究者, I want 每次 run 的 pass/fail 由 fixture 的 pytest exit code 判定, so that 我不需要人工判斷產出品質
9. As a harness 研究者, I want fixture 被完整凍結進版控, so that 三週後跑的 arm 與第一週跑的面對完全相同的起點
10. As a harness 研究者, I want fixture 的 bug 由 mutation script 機械注入, so that bug 藏匿位置不受設計者直覺影響
11. As a harness 研究者, I want fixture 通過 calibration gate 才算合格, so that 素材不會簡單到讓所有 experiment 失去訊號
12. As a harness 研究者, I want 在訊號不足時能加深 fixture 重新生成, so that 難度是我能調整的旋鈕
13. As a harness 開發者, I want 最小 agent 能自主完成修測試的任務, so that 我有一個真實的受測對象而非模擬情境
14. As a harness 開發者, I want agent 的結構遵循一個 agent 一個 class, so that 它的 capability 與 typed state 一目了然
15. As a harness 開發者, I want prompt 不以字串常數存在於 Python 檔中, so that 日後抽出成 registry 時不必翻遍整個 codebase
16. As a harness 開發者, I want harness 的每個 seam 都由一個 experiment 驅動出來, so that 我不會蓋出一個沒有消費者的 framework
17. As a harness 研究者, I want experiment 6 的 effort 掃描作為第一片, so that 我在投入任何複雜機制之前先有 baseline
18. As a harness 研究者, I want 知道單純調整 effort 能省多少, so that 我能判斷後續複雜方案是否換到了等值的東西
19. As a harness 研究者, I want experiment 3 的壓縮成本被計入產生壓縮的那個 arm, so that 壓縮方案不會因為成本被記在別人帳上而虛假勝出
20. As a harness 研究者, I want experiment 3 的 persistent arm 與完整紀錄 arm 起點相同, so that 我能分離出「subagent 活著」單獨值多少
21. As a harness 研究者, I want subagent 使用較便宜的模型時該變因與架構變因分開, so that 我能分辨省下來的是模型單價還是架構設計
22. As a harness 研究者, I want experiment 2 比較三種資料傳遞方式, so that 我知道 pass by reference 在真實資料量下值多少
23. As a harness 研究者, I want experiment 2 在 Claude Code 上也有對照組, so that 我能驗證同樣的原理在既有工具上是否成立
24. As a harness 研究者, I want experiment 1 測試 static 與 dynamic 內容的排列, so that 我知道哪些內容放錯位置會打翻 cache
25. As a harness 研究者, I want experiment 1 觀察 compact 之後 cache 的變化, so that 我知道 context 溢位的真實代價
26. As a harness 研究者, I want experiment 4 比較 tool search 與直接暴露大量 tool, so that 我知道 tool 數量成長時該不該改用延遲載入
27. As a harness 研究者, I want experiment 5 分開測 caveman 與 STE100, so that 我知道可讀性損失較小的方案是否也有相近效果
28. As a harness 研究者, I want experiment 5 以 output token 而非 cache token 衡量, so that 我量的是 output style 真正影響的東西
29. As a harness 研究者, I want experiment 6 比較單一 agent 與先規劃再執行, so that 我知道流程拆解能否降低 thinking 成本
30. As a 未來的維護者, I want spec 明確記載哪些結論不可外推, so that 我不會把合成 fixture 上的絕對值當成真實專案的預期值
31. As a 未來的維護者, I want 兩個 harness 的數字不被放在同一張表比較, so that TTL 差異造成的單價落差不會被誤讀為設計差異
32. As a 未來的維護者, I want 知道目標二為何不在這份 spec 內, so that 我不會以為 MemoryStore 被遺忘了

## Implementation Decisions

### 量測

- 量測分兩個來源，共用同一組型別。自建 harness 取 API 回傳的 usage 物件；Claude Code 解析其 session transcript。兩者的欄位名稱相同，因此只需要一組解析邏輯與兩個 adapter。
- Cost model 依 ADR-0002：以美元表述，各類 token 的權重依 Claude Opus 5 的單價比例（cache read 0.1×、input 1×、cache write 5m 1.25×、cache write 1h 2×、output 5×）。Subagent 使用 Claude Sonnet 5 時套用其自身單價。
- Usage 的細項全部保留：input、output、thinking token、cache read、依 TTL 分流的 cache write、以及逐輪的 iteration 明細。彙總只是呈現方式，不是儲存方式。
- 每個 run 產出一份獨立紀錄，以 experiment 與 arm 分層存放並進版控。原始 usage 完整保留，不做預先彙總。

### Harness 與 TTL

- 自建 harness 固定使用 5 分鐘 cache TTL。主任務是連續互動，請求間隔遠小於 5 分鐘，1 小時 TTL 的雙倍寫入成本換不到對應的命中率。
- Claude Code 固定使用 1 小時 TTL，這是它的行為，不可設定。因此兩個 harness 的百分比不得放在同一張表比較，報告時必須分開呈現。

### Fixture

- 依 ADR-0003：fixture 為生成的 Python 專案，bug 由 mutation script 機械注入，整包凍結進版控。
- 主任務規格：單一失敗測試，但根因位於另一個模組，迫使 agent 探索多個檔案並累積 context。Pass/fail 判準為 fixture 自身 pytest 的 exit code。
- Calibration gate：baseline 執行少於八輪即視為過於簡單，須加深模組層數重新生成。這是 fixture 的驗收條件，不是建議。
- Experiment 2 另配資料分析任務，experiment 4 另配大量 tool 的任務。其餘 experiment 共用主任務。

### Agent 與元件

- Agent 結構依 ADR-0001：class 邊界、typed state field、型別化的 model-facing 邊界依 `nooa-design`；方法該不該存在、介面能不能更窄依 `codebase-design`，agent class 不豁免 deletion test。
- Prompt 不以字串常數存在於 Python 檔中。完整的外部 registry（YAML、版本化、CD 交付、CI 契約測試）不在本切片範圍，但這條約束從第一天生效，因為事後抽離的成本很高。
- `DataRef` 依 ADR-0004 維持薄介面：提供預覽與取得底層物件的途徑，不提供查詢方法。需要什麼資料由模型自行寫 code 取用。這使 harness 需要一個程式碼執行環境，該環境是 experiment 2 本來就要建的。
- `MemoryStore` 依 ADR-0005 延後，不在本 spec 範圍。

### Seam 的產生方式

- 每個 experiment 需要 harness 的某個部位可替換：experiment 1 需要 prompt 組裝順序、2 需要資料傳遞方式、3 需要 subagent 的生命週期與 context 傳遞、4 需要 tool 清單與延遲載入設定、5 需要 system prompt 的 style 段落、6 需要單一 agent 與先規劃再執行兩種流程。
- 這些 seam 一律由其 experiment 驅動產生，不預先建置。理由是每個 seam 屆時都有兩個真實 adapter（該 experiment 的兩個 arm），符合「一個 adapter 是假想的 seam，兩個才是真的」。
- 部分部位不需要抽象。Experiment 5 更換 style 只是替換一段 system prompt 文字，做成可插拔架構屬於過度設計。

### Experiment 的 arm 定義

- **Experiment 1 — prompt 排序**：僅在自建 harness 執行。比較 static 內容、對話紀錄、dynamic 內容的不同排列，並觀察 compact 觸發後 cache 的變化。TTL 選擇（5 分鐘對 1 小時）作為本 experiment 的子項一併測試。
- **Experiment 2 — pass by reference**：自建 harness 比較三個 arm：資料全文進入 context、以 `DataRef` 包裝 in-process 資料、以 `DataRef` 包裝 SQLite。Claude Code 另比較兩個 arm：資料置於 sandbox 由 pandas 取用，對照資料以文字全量塞入。
- **Experiment 3 — subagent 架構**：三個 arm。Arm A 傳遞完整對話紀錄，subagent 每次呼叫全新建立。Arm B 傳遞主 agent 產生的壓縮摘要，subagent 每次呼叫全新建立；產生壓縮所耗的主 agent output token 計入本 arm。Arm C 為 persistent subagent，首次傳遞內容與 Arm A 相同，後續僅傳增量。Subagent 一律使用較便宜的模型，該變因於分析時與架構變因分離。
- **Experiment 4 — 動態 tool 選擇**：比較使用 tool search 搭配延遲載入，對照直接暴露大量 tool。
- **Experiment 5 — output style**：以 output token 衡量，非 cache token。caveman 與 STE100 分別為獨立 arm，另有無 style 的對照組。
- **Experiment 6 — thinking 成本**：effort 掃描（low、medium、high、xhigh）作為 baseline；另比較單一 agent 直接完成任務，對照主 agent 先產出計畫再逐步執行；並測試 low effort 搭配流程拆解的組合。

### 執行順序

依「所需 harness 機制由少到多」排列：experiment 6 的 effort 掃描、experiment 5、experiment 2、experiment 1、experiment 4、experiment 3 與 experiment 6 的流程拆解部分。便宜的 baseline 先建立，複雜機制在有比較基準之後才投入。

### 第一個垂直切片

量測基建、最小 agent、experiment 6 的 effort 掃描。此切片刻意不包含任何 seam 抽象。

## Testing Decisions

好的測試透過公開介面驗證行為，不驗證實作細節。測試名稱使用本專案 `CONTEXT.md` 的詞彙。不 mock 內部協作者，不測 private 方法，不透過側門查驗結果。

本專案為全新 codebase，無既有測試可作為 prior art。以下的 seam 配置即為後續所有測試的先例。

### Seam A — RunRecord 的建構（主要 seam）

從原始 usage 來源到帶成本明細的 run 紀錄。兩個 adapter 餵入：API 的 usage 物件、Claude Code 的 session transcript。兩個真實 adapter 使這成為名副其實的 seam，而非假想的。

絕大多數測試位於此處。它是純函數邊界，不連網、不花錢、可快速重複執行。ADR-0002 的全部計價邏輯在此：四類 token 的權重、cache write 依 TTL 分流、subagent 使用不同模型時的單價切換、以及 experiment 3 Arm B 的壓縮成本歸屬。

此處算錯會使上百次 run 的結論全數失效，且不會產生任何徵兆，因此測試密度應最高。

### Seam B — Experiment runner 的入口

由一個 arm 設定產生一份 run 紀錄。此處僅放置一個 smoke test：以最小 fixture 與最低 effort 執行一次，確認執行任務、收集 usage、換算成本、寫入紀錄的整條管線連通。

不在此處做單元測試，因為每次執行都需要付費的 API 呼叫。

### 刻意不設 seam：Agent 本身

Agent 的正確性由 fixture 自身 pytest 的 exit code 驗證，該 exit code 即為 pass/fail 閘門。額外為 agent 撰寫測試等同於測試模型輸出，屬於驗證想像中的行為而非使用者面向的行為。

### 不再往下切

不為 cost model 單獨開一層更低的 seam。那會使 RunRecord 的建構退化為 pass-through，通不過 deletion test。計價是建構的一部分，不是其下的一層。

## Out of Scope

- `MemoryStore` 與跨 session 記憶。依 ADR-0005 延後至六組 experiment 完成之後。
- 完整的 agent layer。本 spec 只涵蓋 experiment 驅動出來的最小結構。
- 完整的 prompt registry（YAML 來源、版本化、CD 交付、CI 契約測試）。本切片僅保留「Python 檔中不含 prompt 字串」這條約束。
- 以真實開源專案作為 fixture 的驗證。可於六組 experiment 完成後，挑效果最大的一組補跑。
- 兩個 harness 之間的百分比比較。TTL 不同使其單價基準不同。
- 產出品質的細緻評估。閘門僅有 pass/fail。

## Further Notes

### 已知限制

所有數字建立在合成 fixture 之上。合成程式碼結構工整、無死碼、無誤導性註解，缺少真實專案中最耗費 context 的意外複雜度。**arm 之間的相對差異可信，絕對值不可外推至真實專案。** 生成 fixture 與解題模型同屬一個模型家族，構成效度威脅；機械注入 bug 降低但未消除此風險。

### 與 nooa-design 的立場差異

Experiment 6 測試將任務拆解為流程能否降低 thinking 成本。`nooa-design` 的立場相反：其 anti-pattern 表主張優先嘗試單一 agent，並將 workflow graph 列為「Absent by design」。本 experiment 不引用 `nooa-design` 作為依據，而是將其立場視為受測對象。若結果顯示拆解並未較省，該結果即為 `nooa-design` 立場成立的證據，不應視為實驗失敗。

### 觀察來源

Claude Code 的 session transcript 已包含每次 API 呼叫的完整 usage，包括 thinking token 的獨立欄位與依 TTL 分流的 cache write。因此 Claude Code 端的量測不需要額外的遙測設定，也不需要仰賴彙總後的用量指令。
