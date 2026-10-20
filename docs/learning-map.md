# 21 天 SQL 學習地圖

目標：21 天內掌握 SQL 基礎與銀行實務常見需求，並完成一個可展示的作品——
**爬取台股資料 → 寫入 SQL Server → 選股、模擬交易、持倉檢視的 Streamlit 面板**。

- 每天約 2 小時：概念 40 分鐘、實作 60 分鐘、筆記 20 分鐘
- 每天的筆記寫在 `notes/dayXX.md`，記「今天學到的語法」與「踩到的坑」
- 每天的 SQL 存成檔案（`sql/` 底下），這些檔案就是作品的一部分
- 每天最後有「驗收」，全部打勾才算完成；做不完就把剩下的移到隔天，不要硬跳
- 每個 Milestone 結束時打 tag、更新 README 截圖，隨時都有能展示的版本

相關文件：

- [stock-screener-tech-design.md](stock-screener-tech-design.md)：資料表、預存程序、金額規則的完整設計，實作以它為準
- [setup.md](setup.md)：環境建置
- [bank-sql-topics.md](bank-sql-topics.md)：銀行實務主題與面試題

分工：`sql/`、`crawler/`、`backtest/` 由自己寫，`app/`（Streamlit 面板）由 Claude 協作。

---

## 總覽

| 天 | 主題 | Issue | Milestone |
|---|---|---|---|
| 1 | 環境建置、第一個查詢 | [#1](https://github.com/GuanPersonalDev/stock-screener/issues/1) | M1 |
| 2 | SELECT、資料型別、聚合 | [#2](https://github.com/GuanPersonalDev/stock-screener/issues/2) | M1 |
| 3 | 市場資料與快取表的設計 | [#3](https://github.com/GuanPersonalDev/stock-screener/issues/3) | M1 |
| 4 | 爬蟲：TwseClient 與資料清理 | [#4](https://github.com/GuanPersonalDev/stock-screener/issues/4) | M1 |
| 5 | 寫入資料庫：參數化、MERGE、交易 | [#5](https://github.com/GuanPersonalDev/stock-screener/issues/5) | M1 |
| 6 | 每日批次與補抓 | [#6](https://github.com/GuanPersonalDev/stock-screener/issues/6) | M1 |
| 7 | JOIN、對帳、資料品質，M1 收尾 | [#7](https://github.com/GuanPersonalDev/stock-screener/issues/7) | M1 → v0.1 |
| 8 | CTE、視窗函數 I | [#8](https://github.com/GuanPersonalDev/stock-screener/issues/8) | M2 |
| 9 | 視窗函數 II、VIEW | [#9](https://github.com/GuanPersonalDev/stock-screener/issues/9) | M2 |
| 10 | 預存程序：選股 | [#10](https://github.com/GuanPersonalDev/stock-screener/issues/10) | M2 |
| 11 | 索引與執行計畫，M2 收尾 | [#11](https://github.com/GuanPersonalDev/stock-screener/issues/11) | M2 → v0.2 |
| 12 | 帳務資料表設計 | [#13](https://github.com/GuanPersonalDev/stock-screener/issues/13) | M3 |
| 13 | 休市日與除權息爬取 | [#14](https://github.com/GuanPersonalDev/stock-screener/issues/14) | M3 |
| 14 | 下單與圈存 | [#15](https://github.com/GuanPersonalDev/stock-screener/issues/15) | M3 |
| 15 | 逐筆成交、手續費與稅 | [#16](https://github.com/GuanPersonalDev/stock-screener/issues/16) | M3 |
| 16 | T+2 交割與可用額度 | [#17](https://github.com/GuanPersonalDev/stock-screener/issues/17) | M3 |
| 17 | 除權息 | [#18](https://github.com/GuanPersonalDev/stock-screener/issues/18) | M3 |
| 18 | 手續費月退、淨值快照 | [#19](https://github.com/GuanPersonalDev/stock-screener/issues/19) | M3 |
| 19 | 持倉、損益與對帳，M3 收尾 | [#20](https://github.com/GuanPersonalDev/stock-screener/issues/20) | M3 → v0.3 |
| 20 | 最簡版回測 | [#22](https://github.com/GuanPersonalDev/stock-screener/issues/22) | M4 |
| 21 | 作品收尾、面試題自測 | [#24](https://github.com/GuanPersonalDev/stock-screener/issues/24) | M4 → v0.4 |

Claude 負責的面板 Issue 與你的進度並行，不占你的天數：

| Issue | 內容 | 開始條件 |
|---|---|---|
| [#12](https://github.com/GuanPersonalDev/stock-screener/issues/12) | `app/db.py`、選股頁、個股頁 | Day 10 完成 `usp_screen_stocks` |
| [#21](https://github.com/GuanPersonalDev/stock-screener/issues/21) | 首次設定頁、下單頁、持倉頁 | 首次設定頁在 Day 6 後即可做；下單、持倉頁在 Day 19 前完成對應的預存程序與 VIEW |
| [#23](https://github.com/GuanPersonalDev/stock-screener/issues/23) | 回測結果頁 | Day 20 完成 Backtester |

---

## M1 資料庫上線（Day 1–7）

### Day 1｜環境建置、第一個查詢 — #1

**概念**
- 關聯式資料庫的層次：資料庫（database）→ 結構描述（schema）→ 資料表（table）→ 欄位與列
- SQL Server 的預設 schema 是 `dbo`；T-SQL 是 SQL Server 的 SQL 方言
- 為什麼用 Docker：Mac 和 Windows 跑同一個版本、同一份設定

**實作**
1. 照 [setup.md](setup.md) 自己寫 `docker-compose.yml`、`.env`、`.env.example`
2. 加一份 `.gitattributes`（`* text=auto eol=lf`），避免 Windows 把 `.sql` 轉成 CRLF
3. 用 VS Code 的 MSSQL 擴充套件連線，`CREATE DATABASE StockLab;`
4. 跑幾個不需要資料表的查詢：`SELECT GETDATE();`、`SELECT @@VERSION;`

**驗收**
- [ ] 重開 Docker 後資料庫還在（確認 volume 有設定）
- [ ] 密碼只在 `.env`，沒有進 git
- [ ] 能說出 database、schema、table 的差別

### Day 2｜SELECT、資料型別、聚合 — #2

**概念**
- `SELECT … FROM … WHERE … ORDER BY`；T-SQL 用 `TOP n`（其他資料庫是 `LIMIT`）
- 資料型別：`INT`、`NVARCHAR`（中文要用 N 開頭）、`DATE`、`DECIMAL(p, s)`
- **金額與價格一律用 `DECIMAL`，不用 `FLOAT`**——浮點數有誤差，銀行面試常問
- `COUNT`、`SUM`、`AVG`、`GROUP BY`、`HAVING`；`CASE WHEN`；`NULL` 要用 `IS NULL` 比較
- SQL 的邏輯執行順序：`FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY`

**實作**
1. 建練習表 `practice_stocks`，手動 `INSERT` 10 檔熟悉的股票
2. 寫 8 個查詢：價格區間、產業篩選、模糊搜尋、排序取前 3、各產業平均價、`CASE` 分價位
3. 比較 `SELECT 0.1E0 + 0.2E0` 與 `DECIMAL` 相加的結果

**驗收**
- [ ] 能解釋 `WHERE` 與 `HAVING` 的差別
- [ ] 能解釋為什麼 `WHERE` 裡不能用 `SELECT` 取的別名
- [ ] 能解釋 `COUNT(*)` 與 `COUNT(欄位)` 遇到 NULL 的差別

內容較多，做不完的部分移到 Day 3 開頭。

### Day 3｜市場資料與快取表的設計 — #3

**概念**
- 正規化：一件事只存一個地方
- 主鍵、外鍵、`UNIQUE`、`NOT NULL`、`CHECK`、`DEFAULT`；複合主鍵（代號 + 日期）
- DDL 檔依編號執行，已執行過的不改，修改另開新編號——換機器時才能從頭重建

**實作**：依技術文件 §2.2，寫 `sql/ddl/001_*.sql`
- 市場資料：`stocks`、`daily_prices`、`daily_valuations`
- 快取與批次：`crawl_status`、`backfill_requests`、`etl_log`
- 畫 ER 圖（手繪拍照或 dbdiagram.io）放進 `docs/`

**驗收**
- [ ] 重複插入同一檔股票同一天的價格會被擋下
- [ ] 插入不存在的股票代號會被外鍵擋下
- [ ] 收盤價為負數會被 `CHECK` 擋下
- [ ] `stocks` 有上市狀態欄位（下市股票不刪，避免回測的存活者偏差）

### Day 4｜爬蟲：TwseClient 與資料清理 — #4

**概念**
- 證交所資料的格式：千分位逗號、`--` 代表無資料、民國年日期、數字是字串
- 禮貌爬取：請求間隔 3 秒以上，失敗逐次拉長間隔重試
- raw 快取：回應存成 `data/raw/{資料集}/{YYYYMMDD}.json`，檔案存在就不再請求

**實作**
1. 先用瀏覽器打開 TWSE 端點確認 JSON 欄位（端點見 [setup.md](setup.md)）
2. `crawler/cleaners.py`：`parse_number`、`parse_roc_date`
3. `crawler/twse_client.py`：`fetch_daily_quotes`、`fetch_daily_valuations`

**驗收**
- [ ] 非交易日回傳空清單，不丟例外
- [ ] 第二次抓同一天不會發出請求
- [ ] 清理後的數字沒有逗號、沒有 `--`

### Day 5｜寫入資料庫：參數化、MERGE、交易 — #5

**概念**
- **參數化查詢**：永遠不要用字串拼接 SQL，避免 SQL Injection——面試必問
- 交易：`BEGIN TRAN`／`COMMIT`／`ROLLBACK`；一天的資料要嘛全進、要嘛全不進
- 銀行 ETL 的標準做法：先批次寫進暫存表 `#staging`，再用一個 `MERGE` 合併

**實作**：`crawler/repository.py` 的 `StockRepository`（`upsert_*`、`mark_crawl_status`、`write_etl_log`）

**驗收**
- [ ] 同一天寫入兩次，資料不重複
- [ ] 中途故意丟例外，資料庫不會留下半天的資料

### Day 6｜每日批次與補抓 — #6

**概念**
- 冪等（idempotent）：同一天的批次重跑幾次結果都一樣
- `crawl_status` 的三種狀態：`SUCCESS`、`NO_DATA`（休市）、`FAILED`；只有 `FAILED` 會重試

**實作**
1. `crawler/run_daily.py`：抓資料 → 寫入 → 記錄 `crawl_status` 與 `etl_log`（帳務的預存程序到 M3 再接上）
2. `crawler/run_backfill.py`：只抓缺漏的日期，`--force` 才重抓
3. 補抓最近 1 個月資料；用 macOS `launchd` 設定每天 18:00 執行

**驗收**
- [ ] 非交易日在 `etl_log` 記為 `SKIPPED`
- [ ] 補抓中途中斷，重跑只會抓剩下的日期

### Day 7｜JOIN、對帳、資料品質，M1 收尾 — #7

**概念**
- `INNER JOIN`、`LEFT JOIN`、`FULL OUTER JOIN`；JOIN 條件寫錯造成的資料膨脹
- 子查詢：`IN`、`EXISTS`、`NOT EXISTS`
- **對帳**：找出 A 有、B 沒有的資料（`LEFT JOIN … IS NULL`、`NOT EXISTS`、`EXCEPT`）——銀行最常見的需求之一

**實作**：資料品質檢查查詢，存成 `sql/queries/data_quality.sql`
1. 有行情但沒有估值的列，用三種對帳寫法各寫一次
2. 某個交易日缺漏的股票
3. 異常價格：單日漲跌超過 10%（注意：新上市股票前 5 日沒有漲跌幅限制）

**M1 收尾**：README 附 ER 圖與品質查詢結果，打 tag `v0.1`。

**驗收**
- [ ] 三種對帳寫法結果一致
- [ ] 能說出 `NOT IN` 遇到子查詢有 NULL 時會出什麼問題

---

## M2 選股面板（Day 8–11）

### Day 8｜CTE、視窗函數 I — #8

**概念**
- CTE（`WITH … AS`）：把複雜查詢拆成有名字的步驟
- `ROW_NUMBER()`、`RANK()`、`DENSE_RANK()`、`LAG()`、`LEAD()`，搭配 `OVER (PARTITION BY … ORDER BY …)`
- 和 `GROUP BY` 的差別：視窗函數不會把列合併

**實作**
1. 每檔股票的日報酬率（`LAG`）
2. 每檔股票「最新一筆」資料（`ROW_NUMBER() … = 1`，銀行常用來取客戶最新狀態）
3. 每天漲幅前 10 名；每個產業漲幅第一名

**驗收**
- [ ] 能解釋 `ROW_NUMBER`、`RANK`、`DENSE_RANK` 遇到同分時的差別

### Day 9｜視窗函數 II、VIEW — #9

**概念**
- 視窗框架：`ROWS BETWEEN 19 PRECEDING AND CURRENT ROW`
- `VIEW`：面板與報表都讀 VIEW，不直接查原始表

**實作**：`vw_stock_latest_metrics`——最新收盤、5／20 日均線、近 20 日高低點、報酬率、估值

**驗收**
- [ ] 資料不足 20 天的股票，20 日均線是 NULL，不是用不足的天數硬算

### Day 10｜預存程序：選股 — #10

**概念**
- 預存程序：銀行大量使用，批次、報表、權限控管都靠它
- T-SQL 變數（`DECLARE @x`）、參數、`IF`
- 參數為 NULL 代表不篩：`(@p IS NULL OR col <= @p)`
- **parameter sniffing**：第一次呼叫的參數決定了執行計畫，之後的呼叫可能變慢；用 `OPTION (RECOMPILE)` 避免

**實作**：`sql/procedures/usp_screen_stocks.sql`，條件含本益比、殖利率、站上 20 日均線、平均成交量

**驗收**
- [ ] `EXEC usp_screen_stocks @max_pe = 15, @min_yield = 4;` 結果正確
- [ ] 所有參數傳 NULL 時回傳全部股票

完成後 Claude 開始做 #12（選股頁、個股頁）。

### Day 11｜索引與執行計畫，M2 收尾 — #11

**概念**
- 叢集索引與非叢集索引；複合索引的欄位順序；涵蓋索引（`INCLUDE`）
- SARGable：`WHERE YEAR(trade_date) = 2026` 用不到索引，改成日期範圍就可以
- 讀執行計畫：Index Seek 與 Scan 的差別

**實作**
1. `SET STATISTICS IO ON;` 加實際執行計畫，記錄 Day 8–10 查詢的邏輯讀取數
2. 用新編號的 DDL 檔加索引，再量一次，前後數字記在 `notes/day11.md`

**M2 收尾**：README 加選股面板截圖與索引調校數據，打 tag `v0.2`。

**驗收**
- [ ] 至少一個查詢從 Scan 變成 Seek，並能解釋原因

---

## M3 模擬交易與持倉（Day 12–19）

這一段的金額規則、分錄類型、邊界情況都以技術文件 §2.4、§2.5、§6 為準。

### Day 12｜帳務資料表設計 — #13

**概念**
- **只新增的帳**：成交明細與現金流水帳不修改、不刪除，記錯了用沖正分錄抵銷——銀行帳務的核心觀念
- 狀態欄位設計：委託的 `PENDING → FILLED / REJECTED / CANCELLED / EXPIRED`
- 保留 `account_id`：畫面只有一個帳戶，回測另建暫時帳戶

**實作**：新編號的 DDL——`account`、`watchlist`、`orders`、`trades`、`cash_ledger`、`positions`、`nav_snapshots`、`trading_calendar`、`tax_rates`、`corporate_actions`，並在 `stocks` 補上證券類別

**驗收**
- [ ] 能說出每個分錄類型（技術文件 §2.2）對應的業務事件
- [ ] 委託狀態只能是規定的值（`CHECK`）

### Day 13｜休市日與除權息爬取 — #14

**實作**
1. `TwseClient.fetch_holidays`、`fetch_corporate_actions`
2. 寫入 `trading_calendar` 與 `corporate_actions`，接進每日批次

**驗收**
- [ ] 能用 `trading_calendar` 查出任一天的「下兩個交易日」

### Day 14｜下單與圈存 — #15

**概念**
- `THROW`、`TRY … CATCH`、`@@TRANCOUNT`
- **圈存**：下單時先扣住資金，避免超額下單

**實作**：`usp_place_order`、`usp_cancel_order`
- 只接受整張；賣單只能賣「當天開盤前已持有股數 − 未成交賣單」（不允許當沖）
- 買單圈存「今日收盤 × 1.1 + 預估手續費」

**驗收**
- [ ] 可用額度不足時拒絕，並回傳原因
- [ ] 取消委託後圈存釋放

### Day 15｜逐筆成交、手續費與稅 — #16

**概念**
- 逐筆迴圈（`WHILE`）與一次處理整個集合的取捨——面試常見題
- 每筆委託各自一筆交易，單筆失敗不影響其他筆

**實作**：`usp_fill_pending_orders(@trade_date)`
- 用開盤價依委託時間逐筆成交；沒有開盤價（停牌）→ `EXPIRED`
- 手續費 `max(20, floor(價金 × 0.1425%))`，賣出另收證交稅（查 `tax_rates`）
- 更新 `positions` 的移動平均成本

**驗收**
- [ ] 手續費與稅的計算和手算一致
- [ ] 實際價金超過圈存時（沒有漲跌幅限制的股票）會正確處理

### Day 16｜T+2 交割與可用額度 — #17

**實作**
1. `usp_settle(@date)`：把交割日為今天的應收、應付轉為已交割
2. `vw_cash_balance`：交割帳戶餘額、應收、應付、圈存、可用額度

**驗收**
- [ ] 交割日跳過休市日
- [ ] 可用額度 = 交割帳戶餘額 + 應收 − 應付 − 圈存

### Day 17｜除權息 — #18

**實作**：`usp_process_corporate_actions(@date)`
- 權利以除權息前一交易日收盤持股判定
- 現金股利：除息日記應收，發放日入帳；單次 ≥ 20,000 元扣二代健保 2.11%
- 股票股利：除權日增加股數，總成本不變

**驗收**
- [ ] 配股後平均成本正確下降
- [ ] 補充保費只在單次 ≥ 20,000 元時扣

### Day 18｜手續費月退、淨值快照 — #19

**實作**
1. `usp_monthly_fee_rebate(@month)`：依折扣把上個月多收的手續費退回現金帳
2. `usp_take_nav_snapshot(@trade_date)`：淨值 = 現金 + Σ(持股 × 收盤)，重跑用 `MERGE` 覆蓋
3. 把 M3 的預存程序依技術文件 §4.1 的順序接進 `run_daily`

**驗收**
- [ ] 同一天重跑批次，淨值不會重複

### Day 19｜持倉、損益與對帳，M3 收尾 — #20

**實作**
1. `vw_portfolio`：市值、未實現損益（扣預估賣出手續費與稅）、累計股利
2. `vw_realized_pnl`
3. `usp_reconcile_positions`：用 `trades` 依序重算持倉，`FULL OUTER JOIN` 比對 `positions`

**M3 收尾**：模擬一輪「下單 → 成交 → 交割 → 持倉」並截圖，README 寫明刻意簡化的地方（不允許當沖、只交易整張、委託只在下一交易日有效、用圈存模擬、單一帳戶），打 tag `v0.3`。

**驗收**
- [ ] 手動改壞一筆 `positions`，對帳能抓出來

---

## M4 回測與收尾（Day 20–21）

### Day 20｜最簡版回測 — #22

**概念**：回測的目的與陷阱（未來函數、存活者偏差、過度擬合、忽略成本），見技術文件與 [bank-sql-topics.md](bank-sql-topics.md)

**實作**：`backtest/run_backtest.py` 的 `Backtester`
- 一組固定條件、每月調倉、用暫時帳戶重複呼叫預存程序
- 指標：總報酬、最大回撤（`MAX() OVER` 累計最高值）、對比 0050

**驗收**
- [ ] 回測不會動到真實的模擬帳戶
- [ ] 能說明結果有沒有落入上面的陷阱

回測至少需要 1 年資料；資料不夠的話，Day 18 之後先在背景補抓。

### Day 21｜作品收尾、面試題自測 — #24

1. 對照 [bank-sql-topics.md](bank-sql-topics.md) 的面試題自測，答不出來的回頭補
2. 和 Claude 一起完成 README：架構圖、截圖、GIF
3. 打 tag `v0.4`

**展示時可以講的重點**
- 資料表怎麼切（正規化、複合主鍵、只新增的帳）
- 批次重跑為什麼安全（交易、`MERGE`、`crawl_status`）
- T+2 交割與圈存怎麼反映在可用額度
- 選股條件怎麼用視窗函數算、索引調校前後差多少

---

## 進度

| 天 | Issue | 完成日期 | 備註 |
|---|---|---|---|
| 1 | #1 | | |
| 2 | #2 | | |
| 3 | #3 | | |
| 4 | #4 | | |
| 5 | #5 | | |
| 6 | #6 | | |
| 7 | #7 | | |
| 8 | #8 | | |
| 9 | #9 | | |
| 10 | #10 | | |
| 11 | #11 | | |
| 12 | #13 | | |
| 13 | #14 | | |
| 14 | #15 | | |
| 15 | #16 | | |
| 16 | #17 | | |
| 17 | #18 | | |
| 18 | #19 | | |
| 19 | #20 | | |
| 20 | #22 | | |
| 21 | #24 | | |
