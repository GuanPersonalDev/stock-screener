# 兩週 SQL 學習地圖

目標：兩週內掌握 SQL 基礎與銀行實務常見需求，並完成一個可展示的作品——
**爬取台股資料 → 寫入 SQL Server → Streamlit 選股面板**。

- 每天約 2 小時：概念 40 分鐘、實作 60 分鐘、筆記 20 分鐘
- 每天的筆記寫在 `notes/dayXX.md`，記「今天學到的語法」與「踩到的坑」
- 每天的 SQL 存成檔案（`sql/` 底下），不要只在編輯器裡跑完就丟——這些檔案就是作品的一部分
- 每天最後有「驗收」，全部打勾才算完成；做不完就把剩下的移到隔天，不要硬跳

對應的銀行實務主題整理在 [bank-sql-topics.md](bank-sql-topics.md)，環境建置在 [setup.md](setup.md)。

---

## 總覽

| 天 | 主題 | 產出 |
|---|---|---|
| 1 | 環境建置、第一個查詢 | SQL Server 跑起來、`StockLab` 資料庫 |
| 2 | SELECT 基礎、資料型別 | `sql/queries/day02_basics.sql` |
| 3 | 聚合、CASE、NULL | `sql/queries/day03_aggregate.sql` |
| 4 | 資料表設計與約束 | `sql/ddl/001_create_tables.sql` |
| 5 | JOIN 與子查詢 | `sql/queries/day05_join.sql` |
| 6 | 爬蟲：抓 TWSE 資料 | `crawler/fetch_*.py`、原始 CSV |
| 7 | 寫入資料庫、交易、週回顧 | `crawler/load_*.py`、一個月的資料 |
| 8 | CTE、視窗函數 I | `sql/queries/day08_window.sql` |
| 9 | 視窗函數 II、VIEW | `sql/ddl/002_views.sql` |
| 10 | 選股 SQL、預存程序 | `sql/procedures/usp_screen_stocks.sql` |
| 11 | 索引與執行計畫 | `sql/ddl/003_indexes.sql`、前後效能比較筆記 |
| 12 | Streamlit 面板 I：選股表格 | `app/main.py` |
| 13 | 面板 II：個股圖表、批次紀錄 | 個股頁、`etl_log` 表 |
| 14 | 收尾與展示 | README、截圖、面試題自測 |

---

## 第一週：SQL 基礎 + 資料進資料庫

### Day 1｜環境建置、第一個查詢

**概念**
- 什麼是關聯式資料庫：資料庫（database）→ 結構描述（schema）→ 資料表（table）→ 欄位與列
- SQL Server 的預設 schema 是 `dbo`；T-SQL 是 SQL Server 的 SQL 方言

**實作**
1. 照 [setup.md](setup.md) 用 Docker 啟動 SQL Server
2. 用 VS Code 的 MSSQL 擴充套件連線
3. `CREATE DATABASE StockLab;`，切換過去（`USE StockLab;`）
4. 跑幾個不需要資料表的查詢：`SELECT GETDATE();`、`SELECT 1 + 1;`、`SELECT @@VERSION;`

**驗收**
- [ ] 重開 Docker 後資料庫還在（確認 volume 有設定）
- [ ] 能說出 database、schema、table 的差別

### Day 2｜SELECT 基礎、資料型別

**概念**
- `SELECT … FROM … WHERE … ORDER BY`，T-SQL 用 `TOP n` 取前幾筆（其他資料庫是 `LIMIT`）
- 比較運算、`AND`／`OR`、`IN`、`BETWEEN`、`LIKE`
- 資料型別：`INT`、`NVARCHAR`（中文要用 N 開頭）、`DATE`、`DECIMAL(p, s)`
- **金額與價格一律用 `DECIMAL`，不用 `FLOAT`**——浮點數有誤差，銀行面試常問

**實作**
1. 建一張練習表 `practice_stocks`（代號、名稱、產業、收盤價），手動 `INSERT` 10 檔你熟悉的股票
2. 寫 8 個查詢：價格區間、產業篩選、名稱模糊搜尋、依價格排序取前 3……
3. 試試 `SELECT 0.1E0 + 0.2E0` 與 `SELECT CAST(0.1 AS DECIMAL(10,2)) + CAST(0.2 AS DECIMAL(10,2))` 的差別

**驗收**
- [ ] 能解釋為什麼 `N'台積電'` 要加 N
- [ ] 能解釋 `DECIMAL(10, 2)` 兩個數字的意思

### Day 3｜聚合、CASE、NULL

**概念**
- `COUNT`、`SUM`、`AVG`、`MIN`、`MAX`；`GROUP BY` 與 `HAVING` 的差別（`WHERE` 過濾列，`HAVING` 過濾群組）
- SQL 的執行順序：`FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY`
- `CASE WHEN` 做分類；`NULL` 不能用 `=` 比較，要用 `IS NULL`；`COALESCE`、`ISNULL`
- `COUNT(*)` 與 `COUNT(欄位)` 遇到 NULL 的差別

**實作**
1. 各產業的股票數、平均價格；只列出平均價格大於 100 的產業
2. 用 `CASE` 把股價分成「低價／中價／高價」三級，再統計每級幾檔
3. 故意放幾筆 NULL 的產業，觀察聚合結果怎麼變

**驗收**
- [ ] 能說出 SQL 的邏輯執行順序，並解釋為什麼 `WHERE` 裡不能用 `SELECT` 取的別名

### Day 4｜資料表設計與約束

**概念**
- 正規化：一件事只存一個地方（股票基本資料不要在每天的價格裡重複存）
- 主鍵（PRIMARY KEY）、外鍵（FOREIGN KEY）、`UNIQUE`、`NOT NULL`、`CHECK`、`DEFAULT`
- 複合主鍵：每日價格表的唯一性是「股票代號 + 交易日期」

**實作**：自己設計並寫出 DDL，至少包含這三張表（欄位自己決定，寫完再對照提示檢查）

| 表 | 存什麼 | 提示 |
|---|---|---|
| `stocks` | 股票基本資料 | 代號、名稱、產業、市場別 |
| `daily_prices` | 每日行情 | 開高低收、成交量、成交金額；主鍵怎麼設？ |
| `daily_valuations` | 每日本益比、殖利率、股價淨值比 | 和 `daily_prices` 為什麼分開存？ |

畫一張 ER 圖（手繪拍照或用 dbdiagram.io 都可以）放進 `docs/`。

**驗收**
- [ ] 重複插入同一檔股票同一天的價格會被資料庫擋下
- [ ] 插入不存在的股票代號的價格會被外鍵擋下
- [ ] 收盤價為負數會被 `CHECK` 擋下

### Day 5｜JOIN 與子查詢

**概念**
- `INNER JOIN`、`LEFT JOIN`、`FULL OUTER JOIN`；JOIN 條件寫錯造成的資料膨脹
- 子查詢：`WHERE … IN (子查詢)`、`EXISTS`、`NOT EXISTS`
- **對帳**：找出 A 有、B 沒有的資料（`LEFT JOIN … WHERE B.key IS NULL`、`NOT EXISTS`、`EXCEPT`）——銀行最常見的需求之一

**實作**（先手動塞幾天的假資料）
1. 列出每檔股票的名稱與最新收盤價
2. 找出「有基本資料但某天沒有價格」的股票（模擬缺漏檢查）
3. 找出「有價格但沒有估值資料」的列，用三種寫法各寫一次

**驗收**
- [ ] 三種對帳寫法結果一致
- [ ] 能說出 `NOT IN` 遇到子查詢有 NULL 時會出什麼問題

### Day 6｜爬蟲：抓 TWSE 資料

**概念**
- 證交所公開資料：每日全部個股收盤行情、每日本益比／殖利率／股價淨值比
- 資料清理：千分位逗號、`--` 代表無資料、民國年日期、數字是字串
- 禮貌爬取：每次請求間隔 3 秒以上，失敗要重試而不是狂打

**實作**
1. 先用瀏覽器打開 TWSE 的資料頁，確認回傳的 JSON 欄位（端點見 [setup.md](setup.md)，網址若改版以官網為準）
2. 寫 `crawler/fetch_prices.py`：給一個日期，抓當天全部個股行情，清理後存成 CSV
3. 估值資料同理
4. 原始資料存在 `data/raw/`（已在 `.gitignore`）

**驗收**
- [ ] 非交易日（週末、國定假日）不會讓程式當掉
- [ ] CSV 裡的數字欄位沒有逗號、沒有 `--`

### Day 7｜寫入資料庫、交易、週回顧

**概念**
- 用 Python 連 SQL Server（`pymssql` 或 `pyodbc`）
- **參數化查詢**：永遠不要用字串拼接 SQL，避免 SQL Injection——面試必問
- 交易（transaction）：`BEGIN TRAN`／`COMMIT`／`ROLLBACK`；一天的資料要嘛全進、要嘛全不進
- 重複執行要安全（idempotent）：用 `MERGE` 或「先刪該日再寫入」做 upsert

**實作**
1. 寫 `crawler/load_prices.py`：讀 CSV → 批次寫入 `daily_prices`
2. 同一天跑兩次，資料不能重複
3. 補齊最近一個月的資料（約 20 個交易日）

**週回顧**：不看筆記，重寫 Day 3 和 Day 5 的查詢各兩題。

**驗收**
- [ ] `SELECT COUNT(*) FROM daily_prices` 大約是「股票數 × 交易日數」
- [ ] 程式中途故意丟例外，資料庫不會留下半天的資料

---

## 第二週：進階查詢 + 選股面板

### Day 8｜CTE、視窗函數 I

**概念**
- CTE（`WITH … AS`）：把複雜查詢拆成有名字的步驟
- 視窗函數：`ROW_NUMBER()`、`RANK()`、`DENSE_RANK()`、`LAG()`、`LEAD()`，搭配 `OVER (PARTITION BY … ORDER BY …)`
- 和 `GROUP BY` 的差別：視窗函數不會把列合併

**實作**
1. 每檔股票的日報酬率：`(今日收盤 - 昨日收盤) / 昨日收盤`，用 `LAG`
2. 每檔股票「最新一筆」資料：`ROW_NUMBER() … = 1`（銀行常用來取客戶最新狀態）
3. 每天漲幅前 10 名；每個產業漲幅第一名

**驗收**
- [ ] 能解釋 `ROW_NUMBER`、`RANK`、`DENSE_RANK` 遇到同分時的差別

### Day 9｜視窗函數 II、VIEW

**概念**
- 視窗框架：`ROWS BETWEEN 19 PRECEDING AND CURRENT ROW`
- 移動平均、累計值、區間最高最低
- `VIEW`：把常用查詢包起來，面板與報表都讀 VIEW

**實作**
1. 5 日、20 日移動平均
2. 近 20 日最高價、最低價；收盤價距離區間高點幾 %
3. 建立 `vw_stock_latest_metrics`：每檔股票最新一天的收盤、均線、報酬率、本益比、殖利率

**驗收**
- [ ] 資料不足 20 天的股票，20 日均線要顯示 NULL 而不是用不足的天數硬算（想想怎麼判斷）

### Day 10｜選股 SQL、預存程序

**概念**
- 預存程序（Stored Procedure）：銀行大量使用，批次、報表、權限控管都靠它
- T-SQL 變數（`DECLARE @x`）、參數、`IF`、`TRY … CATCH`

**實作**
1. 寫出選股條件，例如：本益比 < 15、殖利率 > 4%、收盤站上 20 日均線、近 5 日平均成交量 > 1000 張
2. 包成 `usp_screen_stocks`，條件都是參數，參數為 NULL 時代表不篩這個條件
3. 用不同參數組合呼叫，確認結果合理

**驗收**
- [ ] `EXEC usp_screen_stocks @max_pe = 15, @min_yield = 4;` 能正確回傳
- [ ] 所有條件都傳 NULL 時回傳全部股票

### Day 11｜索引與執行計畫

**概念**
- 叢集索引（clustered）與非叢集索引（nonclustered）；主鍵預設就是叢集索引
- 複合索引的欄位順序；涵蓋索引（`INCLUDE`）
- SARGable：`WHERE YEAR(trade_date) = 2026` 用不到索引，改成日期範圍就可以
- 讀執行計畫：Index Seek 與 Index/Table Scan 的差別

**實作**
1. 打開 `SET STATISTICS IO ON;` 與實際執行計畫，記錄 Day 8–10 幾個查詢的邏輯讀取數
2. 加索引或改寫查詢，再量一次，前後數字記在 `notes/day11.md`

**驗收**
- [ ] 至少一個查詢從 Scan 變成 Seek，並能解釋原因

### Day 12｜Streamlit 面板 I：選股表格

**實作**
1. `app/main.py`：側邊欄放選股條件（滑桿、輸入框）
2. 按下按鈕 → 呼叫 `usp_screen_stocks` → 顯示結果表格
3. 連線字串從 `.env` 讀，不寫死在程式裡

**驗收**
- [ ] `streamlit run app/main.py` 能篩出結果
- [ ] 密碼不在任何會進 git 的檔案裡

### Day 13｜面板 II：個股圖表、批次紀錄

**實作**
1. 點選某檔股票 → 顯示收盤價與 5／20 日均線的折線圖
2. 建 `etl_log` 表：每次爬蟲執行記一筆（日期、筆數、成功或失敗、錯誤訊息）
3. 面板上顯示「資料更新至哪一天」，從 `etl_log` 或 `MAX(trade_date)` 取
4. 寫一個資料品質檢查查詢：重複、缺漏、異常價格（例如單日漲跌超過 10%）

**驗收**
- [ ] 爬蟲失敗時 `etl_log` 有紀錄
- [ ] 面板能看出資料是不是最新的

### Day 14｜收尾與展示

1. README：專案目的、架構圖、資料表設計、如何啟動、截圖
2. 錄一段 30 秒的操作 GIF 放進 README
3. 對照 [bank-sql-topics.md](bank-sql-topics.md) 的面試題自測，答不出來的回頭補
4. 推上 GitHub

**展示時可以講的重點**
- 資料表為什麼這樣切（正規化、複合主鍵）
- 爬蟲重複執行為什麼安全（交易 + upsert）
- 為什麼用參數化查詢
- 選股條件怎麼用視窗函數算、索引怎麼加、效能差多少

---

## 進度

| 天 | 完成日期 | 備註 |
|---|---|---|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |
| 6 | | |
| 7 | | |
| 8 | | |
| 9 | | |
| 10 | | |
| 11 | | |
| 12 | | |
| 13 | | |
| 14 | | |
