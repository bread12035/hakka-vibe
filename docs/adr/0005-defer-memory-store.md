---
status: accepted
---

# `MemoryStore` 延後到六個 experiment 完成之後

專案的第二個目標是建立完善的 agent layer 與 memory layer，但這份 spec 不含 `MemoryStore`。原因是六個 experiment 沒有任何一個需要跨 session 記憶，現在實作等於一個 adapter、零個真實消費者 —— `codebase-design` 判定的 hypothetical seam。

## Consequences

- 目標二並未放棄，而是排到有數據之後。experiment 的結果會直接決定 agent layer 與 memory layer 該長什麼樣；在拿到數據前定案，等於放棄做這整件事的理由。
- 實作時預計採用 markdown 檔案，而非 `nooa-design` 規定的「single human-readable SQLite file」。這個偏離的理由需要在動工時補一份 ADR。
