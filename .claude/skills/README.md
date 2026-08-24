# Skills（來自 mattpocock/skills）

本資料夾放的是給 code agent 參考的 skills，內容原封不動取自 [mattpocock/skills](https://github.com/mattpocock/skills)。

- 上游 repo：https://github.com/mattpocock/skills
- 上游版本：`v1.2.3`
- 上游 commit：`5b15a47f2d7150f545fbcacbfe381787fc0230dc`（2026-08-21）
- 授權：MIT（見本資料夾的 [LICENSE](./LICENSE)）

上游把 skills 分成 `skills/engineering/`、`skills/productivity/` 等分類；這裡攤平成 `.claude/skills/<name>/`，Claude Code 才能自動載入。每個 skill 內部的相對連結（例如 `tdd/tests.md`）都在自己的資料夾內，攤平不影響。

## 收錄的 skills

### 主要（本次指定要用的）

| Skill | 用途 |
| --- | --- |
| `grill-me` | 一次一輪、逼問到底的訪談，把計畫或設計問清楚 |
| `grill-with-docs` | 同上，但邊問邊產出文件（ADR + 詞彙表） |
| `to-spec` | 把目前對話直接整理成 spec 並發到 issue tracker（不再訪談） |
| `to-tickets` | 把計畫／spec／對話拆成 tracer-bullet 票，並標出彼此的 blocking 關係 |
| `implement` | 依照 spec 或票開始實作，過程用 TDD，完成後跑 code review 並 commit |
| `tdd` | red-green-refactor 的準則：什麼是好測試、seam 放哪、反模式 |
| `code-review` | 用兩條軸線審查 diff：Standards（是否符合本 repo 規範）與 Spec（是否忠實實作需求） |
| `improve-codebase-architecture` | 掃描 codebase 找出 deepening 機會，出 HTML 報告，再針對選定項目逼問 |

> 註：指定清單裡的 `grill-with-doc` 在上游叫 `grill-with-docs`；`implementation` 對應的是 `implement`（上游沒有叫 `implementation` 的 skill）。

### 相依（上面那些 skill 會呼叫，所以一起收錄）

| Skill | 被誰用到 |
| --- | --- |
| `grilling` | `grill-me`、`grill-with-docs`、`improve-codebase-architecture` 實際的訪談引擎 |
| `domain-modeling` | `grill-with-docs`、`improve-codebase-architecture`（產出 `CONTEXT.md` 與 ADR） |
| `codebase-design` | `tdd`、`improve-codebase-architecture` 共用的設計詞彙（module / interface / depth / seam / adapter / leverage / locality） |
| `setup-matt-pocock-skills` | `to-spec`、`to-tickets`、`code-review` 需要的 `docs/agents/*.md` 設定，第一次使用前跑一次 |

沒有收錄上游其他 skills（`triage`、`research`、`prototype`、`wizard` 等）。要補的話，從上游同一個 commit 複製對應資料夾進來即可，記得一併確認它有沒有呼叫別的 skill。

## 使用前置作業

`to-spec`、`to-tickets`、`code-review` 都預期 repo 裡有 `docs/agents/issue-tracker.md`。第一次使用前先跑：

```
/setup-matt-pocock-skills
```

它會問你 issue tracker（GitHub / GitLab / 本地 markdown）、triage label 詞彙、domain 文件擺放位置，然後把設定寫進 `docs/agents/`。

## 更新方式

```bash
git clone --depth 1 https://github.com/mattpocock/skills.git /tmp/mp-skills
# 把要更新的資料夾覆蓋回 .claude/skills/<name>/，並移除裡面的 agents/（那是給 OpenAI harness 用的）
```

更新後記得把本檔案開頭的上游 commit 一併改掉。
