# Results

每一次 run 的原始紀錄，依 experiment 與 arm 分層，進版控。

```
results/<experiment>/<arm>/<run>.json
```

每份檔案只存**原始 usage** 與該次 run 的身分（experiment、arm、run、model、pass/fail）。
Token 細項與成本都在讀取時即時算出，不預先彙總——修正 cost model 會重新為所有歷史 run 計價，
而不是讓它們停留在寫入當天的算法上。

哪些欄位重要並未定案：`thinking_tokens` 與 cache write 的 TTL 分流都是有人去看了才發現有用的。
存彙總結果等於丟掉下一個問題的答案，代價是重跑全部 72 次付費 run。
