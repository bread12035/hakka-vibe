# 02: Fixture 生成器與機械注入 bug

**What to build:** 生成一個凍結的 Python 專案作為 fixture，並以 mutation script 機械式注入一個 bug。注入前後的差異就是 bug 的完整說明。依 ADR-0003，採用生成而非現成專案，是為了讓難度成為可調的旋鈕。

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] 生成的專案有多個模組與一套可執行的 pytest 測試
- [ ] Bug 由 mutation script 隨機選定位置注入，做標準變異（比較運算子反向、off-by-one、參數順序對調），非人工設計藏匿位置
- [ ] 注入的 bug 位於某個模組，而失敗的測試位於另一個模組，迫使探索跨檔案進行
- [ ] 注入後 pytest 為紅，還原後為綠
- [ ] Fixture 整包凍結進版控，bug 注入為獨立 commit
- [ ] 模組層數可調整，以便日後加深後重新生成
