# AGENTS.md

本 repo 的 agent 工作流程說明統一寫在 [CLAUDE.md](./CLAUDE.md)，skills 本體放在 `.claude/skills/`（來源與版本見 `.claude/skills/README.md`）。

摘要：釐清需求用 `grill-me` / `grill-with-docs`；需求轉任務用 `to-spec` → `to-tickets`；寫 code 用 `implement` + `tdd`；審核架構用 `code-review` / `improve-codebase-architecture`。第一次使用前先跑 `setup-matt-pocock-skills`。
