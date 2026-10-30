# Day 3｜市場資料與快取表的 DDL、ER 圖

日期：2026-10-24 ～ 2026-10-30　對應 Issue：#3

## 做了什麼

1. 依技術文件 §2.2，在 `sql/ddl/` 寫六個 DDL 檔，依編號執行
2. 每張表寫完後，用 `BEGIN TRAN … ROLLBACK` 插入測試資料，確認約束會擋下錯誤資料
3. 在 `docs/er-diagram.md` 用 Mermaid 畫 ER 圖，再用 MSSQL 擴充套件的 Visualize and Design Schema 對照資料庫實際結構

| 檔案 | 資料表 | 用途 |
|---|---|---|
| `001_stocks.sql` | `stocks` | 股票基本資料，其他市場資料表的父表 |
| `002_daily_prices.sql` | `daily_prices` | 每日開高低收、成交量、成交金額 |
| `003_daily_valuations.sql` | `daily_valuations` | 每日本益比、殖利率、股價淨值比 |
| `004_crawl_status.sql` | `crawl_status` | 每個資料集每天的抓取結果，決定要不要重抓 |
| `005_backfill_requests.sql` | `backfill_requests` | 從面板送出的回補請求 |
| `006_etl_log.sql` | `etl_log` | 每次 ETL 的執行紀錄與錯誤訊息 |

## DDL 檔的規則

- DDL（Data Definition Language）定義結構：`CREATE`、`ALTER`、`DROP`。DML（Data Manipulation Language）操作資料：`SELECT`、`INSERT`、`UPDATE`、`DELETE`。
- 檔案依編號執行；已執行或已 commit 的檔案不改，要修改就另開新編號（migration）。換機器時才能從 001 依序重建出一樣的結構。
- 每個檔案都要能重複執行。用 `IF OBJECT_ID(N'dbo.x', N'U') IS NULL` 包住 `CREATE TABLE`，表已存在就跳過；正式的 DDL 不用 `DROP`。
- `OBJECT_ID` 的第二個參數是物件類型：`U` 是使用者資料表，另有 `V`（view）、`P`（stored procedure）、`PK`、`F`（外鍵）、`C`（CHECK）。
- `USE StockLab;` 切換到目標資料庫；`GO` 是批次分隔符號，不是 T-SQL 指令。
- 一律寫 `dbo.` 前綴。`sa` 的預設 schema 是 `dbo`，但明確寫出來比較不會建錯地方，之後的 `SCHEMABINDING` 也要求一定要寫。
- 關鍵字不分大小寫。預設定序（collation）不分大小寫，所以 `CHECK (x IN ('LISTED'))` 也會接受 `'listed'`。

### 重複執行的陷阱

`IF OBJECT_ID … IS NULL` 讓第二次執行直接跳過。改完檔案再執行，資料庫裡留著的還是舊版本的表，而且不會有任何錯誤訊息。001 就遇到這個狀況：表是空的、也還沒 commit，所以手動 `DROP TABLE` 後重新執行。表裡有資料或已 commit 之後，就只能用新編號的 `ALTER TABLE` 修改。

## 約束

| 約束 | 作用 | 命名 |
|---|---|---|
| `PRIMARY KEY` | 唯一且不可 NULL，一張表只有一個 | `PK_表名` |
| `FOREIGN KEY … REFERENCES` | 值必須存在於父表 | `FK_表名_父表` |
| `UNIQUE` | 唯一，但可以有一個 NULL | `UQ_表名_欄位` |
| `CHECK` | 條件為 FALSE 時擋下 | `CK_表名_欄位` |
| `DEFAULT` | 插入時省略該欄就填預設值 | `DF_表名_欄位` |
| `NOT NULL` | 不可為 NULL；不算具名約束 | — |

- 約束名稱在同一個 schema 內不能重複，所以名稱要帶表名。沒命名時 SQL Server 會產生 `PK__stocks__A1B2C3…` 這種亂碼名稱，之後要 `ALTER` 或看錯誤訊息都很難辨認。
- 寫在欄位那一行是 inline，寫在欄位清單最後是 table-level。複合主鍵、跨欄位的 `CHECK`（例如 `high_price >= low_price`）只能寫成 table-level。
- `DEFAULT` 要寫在欄位那一行：`col 型別 NOT NULL CONSTRAINT DF_x DEFAULT 值`。
- 同一個約束只寫一次。欄位那一行已經寫了 `CHECK`，table-level 就不要再寫一份。

### 容易誤會的行為

- `CHECK` 遇到 NULL 會通過：`NULL >= 0` 的結果是 UNKNOWN，不是 FALSE。要禁止 NULL 得另外加 `NOT NULL`。
- `DEFAULT` 只在插入時省略該欄才生效；明確寫 `NULL` 進去，存的就是 NULL。
- 外鍵的型別要跟父表一致，父表要先建立。父表的資料被子表參照時刪不掉。
- 外鍵不會自動建立索引。
- 結果類的狀態欄位不設 `DEFAULT`。`crawl_status.status` 原本預設 `'NO_DATA'`，程式漏寫狀態時，會把那天默默標成「沒有資料、不用重抓」；不設預設值，漏寫就會被 `NOT NULL` 擋下來。

## 複合主鍵

`daily_prices`、`daily_valuations` 的主鍵是 `(stock_id, trade_date)`：同一檔股票可以有很多天，同一天可以有很多檔股票，但同一檔股票同一天只能有一筆。

- 單獨用 `stock_id` 當主鍵，一檔股票只能存一天；單獨用 `trade_date`，一天只能存一檔股票。
- 欄位順序會影響索引。`stock_id` 放前面，適合「某檔股票某段期間」的查詢，這也是回測最常用的查法。
- `crawl_status` 同理，主鍵是 `(dataset, trade_date)`。
- 沒有自然鍵的表（`backfill_requests`、`etl_log`）用 `INT IDENTITY(1,1)` 自動編號。編號可能跳號（交易 rollback 也會用掉號碼），取剛插入的編號用 `SCOPE_IDENTITY()`。

## 資料型別的選擇

| 欄位 | 型別 | 原因 |
|---|---|---|
| `stock_id` | `VARCHAR(10)` | 代號有英文（`2881A`、`00631L`、`00679B`）和開頭的 0（`0050`），不能用 `INT` |
| `stock_name`、`industry`、`market` | `NVARCHAR(50)` | 含中文；`VARCHAR` 會把中文存成 `???` |
| 開高低收 | `DECIMAL(10,2)` | 價格要精確，不用 `FLOAT` |
| `trade_volume`、`trade_value` | `BIGINT` | 成交金額會上億，`INT` 上限約 21 億會溢位 |
| `is_force_backfill` | `BIT` | 布林值；只有 0、1、NULL，查詢寫 `= 1`，T-SQL 沒有 `TRUE` |
| `created_time` | `DATETIME2(0)` | 精確到秒；`DATETIME` 會把時間四捨五入到 3.33 毫秒 |
| `error_message` | `NVARCHAR(MAX)` | 錯誤訊息可能含中文且長度不定 |

- `DECIMAL` 的儲存空間依總位數分級：1～9 位 5 bytes、10～19 位 9 bytes、20～28 位 13 bytes、29～38 位 17 bytes。
- `SYSUTCDATETIME()` 回傳 UTC 時間，台灣是 UTC+8。轉成台灣時間：`AT TIME ZONE 'UTC' AT TIME ZONE 'Taipei Standard Time'`。`trade_date` 是台灣的交易日，直接存 `DATE`，不轉 UTC。
- 狀態欄位慣例叫 `status`，值用大寫英文（`SUCCESS`、`FAILED`、`CANCELLED`）。布林欄位以 `is_`、`has_` 開頭。
- IDE 把字變色不代表是保留字。`status`、`date`、`name`、`type` 都可以當欄位名稱；要避開的是 `order`、`user`、`key` 這類真正的保留字。

## 停牌的處理

`daily_prices` 的開高低收原本設 `NOT NULL`。停牌當天證交所沒有成交價，整列會插不進去，所以改成允許 NULL。`CHECK (close_price >= 0)` 遇到 NULL 會通過，不影響負數的檢查。

## ER 圖

ER 圖（Entity-Relationship Diagram）把表、欄位、鍵和表之間的關係畫成一張圖。DDL 給資料庫執行，ER 圖給人看，兩者必須一致。

- `stocks ||--o{ daily_prices`：一檔股票對零到多筆日價，`daily_valuations` 同理。
- `crawl_status`、`backfill_requests`、`etl_log` 是批次控制用的表，跟市場資料沒有外鍵關係，單獨畫出來。
- 複合主鍵的兩個欄位都要標 PK。只標 `trade_date`，看起來會像一天只能存一筆。
- Mermaid 的型別不能有逗號，`DECIMAL(10,2)` 只寫 `decimal`。
- Mermaid 的關係是表對表，線接在哪一列只是排版位置，連接的欄位看線上的標籤。

MSSQL 擴充套件的 Visualize and Design Schema 能從資料庫反向產生圖，適合用來驗證手寫的 ER 圖。但它沒有一對多的符號，也分不出 PK 和 FK。

## 踩到的坑

- 001：漏了主鍵；`BOND_ETF` 打成 `BOUND_ETF`；約束沒命名；欄位清單最後多一個逗號。
- 001 改完重新執行沒有生效，因為 `IF OBJECT_ID` 讓它跳過了，資料庫裡還是舊版本。
- 002：原本沒有 `CHECK`，負的收盤價插得進去；價格設 `NOT NULL` 擋掉停牌的資料。
- 002：欄位 `date` 改名為 `trade_date`、`trade_price` 改名為 `trade_value`，名稱要能看出內容。
- 004：`status` 的 `DEFAULT 'NO_DATA'` 會把錯誤藏起來，拿掉。
- 006：`error_message` 原本用 `VARCHAR(MAX)`，中文錯誤訊息存成 `????:TWSE ?? 503`，改成 `NVARCHAR(MAX)` 後正確存成 `連線逾時：TWSE 回應 503`。
- ER 圖：第一版只有 `trade_date` 標 PK，`stock_id` 漏標。

## 驗收

- [x] 重複插入同一檔股票同一天的價格會被擋下（`PK_daily_prices`）
- [x] 插入不存在的股票代號會被外鍵擋下（`FK_daily_prices_stocks`）
- [x] 收盤價為負數會被 `CHECK` 擋下（`CK_daily_prices_close_price`）
- [x] `stocks` 有上市狀態欄位 `listing_status`（下市股票不刪，避免回測的存活者偏差）
- [x] ER 圖放在 `docs/er-diagram.md`
