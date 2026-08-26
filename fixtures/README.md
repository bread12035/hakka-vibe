# Fixtures

被測 agent 要操作的凍結素材。**這個 README 刻意放在 fixture root 之外**——agent 只會被指向
`fixtures/pipeline/`，不該讀到關於 bug 的任何資訊。

## pipeline

一條分層的 pipeline，`stage_0` 呼叫 `stage_1`，依此類推。測試只 import `stage_0`，
而 bug 一定被注入在 `stage_1` 以下，所以找出原因必須讀過失敗測試指名的那個檔案之外。

| | |
| --- | --- |
| 生成參數 | `depth=8, seed=20260826` |
| 注入參數 | `inject_bug(seed=1)` |
| 重現方式 | `generate_fixture(Path("fixtures/pipeline"), depth=8, seed=20260826)` 後 `inject_bug(fixture, seed=1)` |

### 尚未通過 calibration gate

ADR-0003 要求 baseline 執行少於八輪即判定素材過於簡單、須加深後重新生成。
`depth=8` 是**未經量測的初始猜測**——calibration gate（ticket 04）需要真實 API 呼叫，
在生成當下的環境無法執行。首次在有憑證的環境跑過 baseline 之後，必須回來確認或調整 depth。
