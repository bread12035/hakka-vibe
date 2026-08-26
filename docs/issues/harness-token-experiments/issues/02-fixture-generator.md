# 02: Fixture 生成器與機械注入 bug

**What to build:** 生成一個凍結的 Python 專案作為 fixture，並以 mutation script 機械式注入一個 bug。注入前後的差異就是 bug 的完整說明。依 ADR-0003，採用生成而非現成專案，是為了讓難度成為可調的旋鈕。

**Blocked by:** None (can start immediately)

**Status:** done

- [x] 生成的專案有多個模組與一套可執行的 pytest 測試
- [x] Bug 由 mutation script 隨機選定位置注入，做標準變異（比較運算子反向、off-by-one、參數順序對調），非人工設計藏匿位置
- [x] 注入的 bug 位於某個模組，而失敗的測試位於另一個模組，迫使探索跨檔案進行
- [x] 注入後 pytest 為紅，還原後為綠
- [x] Fixture 整包凍結進版控，bug 注入為獨立 commit
- [x] 模組層數可調整，以便日後加深後重新生成

## Comments

兩個在實作中被抓到、否則會靜默毀掉素材的問題：

1. **Stale bytecode。** Python 用 (mtime, size) 判定 `.pyc` 是否過期，而 `+ 1`→`+ 2` 與
   `combine(a, b)`→`combine(b, a)` 兩種變異**不改變檔案大小**。探測時在同一個 mtime tick 內
   改了又還原，會沿用舊的 bytecode，導致「這個變異沒有效果」的錯誤結論。已改為 `-B` 加
   `PYTHONDONTWRITEBYTECODE=1`。

2. **`comparison` 變異原本永遠無效。** 隨機 THRESHOLD 幾乎不可能剛好等於 carried 值，
   `<=` 改 `<` 因此沒有行為差異，三種變異只有兩種可用。已改為每個 stage 的 THRESHOLD
   等於實際流到該層的值，邊界必被踩到。

生成器只回報「經驗證確實會改變輸出」的 site，所以 `inject_bug` 不可能注入一個 fixture
自己測不出來的 bug。site 清單只存在記憶體中，**不寫進 fixture 目錄**——一份列出 bug
可能位置的檔案等於把答案交給被測的 agent。

`fixtures/pipeline` 的 `depth=8` 是**未經量測的猜測**，尚未通過 calibration gate（ticket 04），
已記在 `fixtures/README.md`。
