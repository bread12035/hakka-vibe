---
status: accepted
---

# `src/hakka_vibe/` 依角色分子套件，不維持扁平單一目錄

`src/hakka_vibe/` 原本是 20 個檔案攤平在同一層的單一 package。隨著 seam 一個一個由 experiment 驅動長出來（ticket 01–15），檔案數跟著漲到 20 個，但彼此的分類關係只能靠檔名猜——讀者得先讀過所有檔案，才知道 `output_style.py` 跟 `decoy_tools.py` 是同一種東西（可替換的 seam），`call.py` 跟 `report.py` 又是另一種東西（量測管線）。

改為四個依角色分的子套件：

- **`agents/`** — 三個 agent class，一個 class 一個檔（`nooa-design` 明文規定：「Agent | one Python class | One agent, one class, one file」，這是唯一被上游 skill 直接管到檔案佈局的部分）。`fixer.py`／`analyst.py`／`subagent.py`，檔名對齊各自的 prompt key 前綴（`fixer.*`／`analyst.*`／`subagent.*`）。
- **`seams/`** — 會被至少一組 experiment 當變因替換掉的模組：`prompt_layout.py`、`output_style.py`、`decoy_tools.py`、`dataref.py`、`sandbox.py`、`compress.py`、`delegation.py`。原本混在 `subagent.py` 裡的 `DelegationMode`／`context_for_call()` 拆成獨立的 `delegation.py`——這兩者是 experiment 3 的變因本體，`Subagent` 這個 class 的能力在三個 arm 之間不變，混在同一檔案裡模糊了這條界線。
- **`measurement/`** — 量測管線：`call.py`、`cost.py`、`run_record.py`、`claude_code_adapter.py`、`report.py`，以及原本叫 `experiment.py` 的 arm runner，改名 `arm_runner.py`——它跟既有的 `experiments/`（六組實驗本體所在的子套件）名字太像，容易讓人誤以為是同一層。
- **`fixture/`** — 素材生成與驗收：原本的 `fixture.py` 改名 `generator.py`（避免 `fixture/fixture.py` 這種目錄與檔案同名的寫法），`calibration.py` 隨遷入。

`prompts.py` 與 `tool_schema.py` 留在 package 根目錄不動：兩者是四個分類共用的基礎設施，不屬於任何一類。`experiments/` 子套件本身不動——它是消費 `seams/` 的那一層，概念上跟另外四個分類平行，不是其中之一。

## Considered Options

- **維持扁平單一目錄**：否決。是重整前的實際狀況，理由見上——分類關係不可見，新增檔案時該放哪裡全憑感覺，不是規則。
- **依 experiment 編號分目錄**（`exp1/`、`exp2/`……）：否決。`run_record.py`、`cost.py` 這類核心量測邏輯不屬於任何單一 experiment，會被迫複製或掛在某個編號底下，製造假的歸屬關係。
- **`prompts/` 也依 nooa-design 完整 registry 願景重新分層**（例如 `prompts/agents/fixer/system.yaml`，路徑鏡射 `agents.fixer`）：否決，非本次範圍。`nooa-design/references/prompt-registry.md` 描述的是尚未建置的完整 YAML registry；本專案目前的 `prompts.py` 是刻意的簡化版（其自身 docstring：「完整的 registry……不是建置這個切片的範圍」），用的是扁平字串 key（如 `fixer.system`），不是 import path 鏡射。等完整 registry 真的動工，`agents/` 底下的分包會不會影響它的路徑慣例，屆時另開 ADR。

## Consequences

- 20 個檔案的 import path 全部改變；用 `git mv` 逐檔搬動，保留個別歷史。
- 新增檔案時該歸在哪一類，寫進 `CLAUDE.md`，`/implement` 執行任務時一併參考。
- `tests/` 鏡射同一套分類（`tests/agents/`、`tests/seams/`……），維持「測試幾乎跟 src 一對一」的既有慣例；`test_call_smoke.py` 因為橫跨多個分類（用真實 API 依序打過每一組 experiment）留在 `tests/` 根目錄，不強塞進單一分類。
