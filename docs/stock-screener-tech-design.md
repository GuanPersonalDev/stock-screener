# stock-screener — 技術設計文件

> 生成時間：2026-10-20
> 所屬專案：sql-stock-screener
> 關聯 GitHub：尚未建立（待 progress-planner 建立 Milestone / Issue，repo：GuanPersonalDev/stock-screener）

---

## 1. 功能概述

系統每天爬取台灣證券交易所（TWSE）上市證券的行情、估值、除權息與休市日資料，存進 MS SQL Server（Docker，Apple Silicon 使用 linux/amd64 加 Rosetta）。使用者可用條件選股，以模擬資金下單（隔日開盤價成交、T+2 交割），並在 Streamlit 面板查看持倉、損益與淨值曲線，也能做簡易回測。交易與帳務邏輯全部放在預存程序，Python 只負責串接。

本系統為單一使用者、單一模擬帳戶；資料表保留 `account_id`，回測另建暫時帳戶，不動真實模擬帳戶。

專案不附任何市場資料（證交所資料再散布授權未確認）。首次開啟面板時由使用者決定要補抓多久以前的資料。

---

## 2. 模組清單與職責

### 2.1 Python 與預存程序模組

| 模組 | 所在層級 | 職責 | 檔案路徑 |
|---|---|---|---|
| TwseClient | 爬蟲 | 向 TWSE 取得行情、估值、除權息、休市日，含快取、重試與限速 | crawler/twse_client.py |
| cleaners | 爬蟲 | 數字與民國日期的字串解析 | crawler/cleaners.py |
| StockRepository | 爬蟲 | 批次寫入資料庫、維護 crawl_status 與 etl_log、呼叫每日預存程序 | crawler/repository.py |
| run_daily | 爬蟲 | 每日批次的串接順序 | crawler/run_daily.py |
| run_backfill | 爬蟲 | 處理補抓需求 | crawler/run_backfill.py |
| db | 面板 | 面板的資料庫存取（查詢 VIEW、呼叫預存程序） | app/db.py |
| 面板頁面 | 面板 | 首次設定、選股、個股、下單、持倉、回測結果 | app/pages/ |
| Backtester | 回測 | 以暫時帳戶重複呼叫預存程序，計算回測指標 | backtest/run_backtest.py |
| 預存程序 | 預存程序 | 選股、下單、成交、交割、除權息、月退、淨值、對帳 | sql/procedures/ |
| 資料表與 VIEW | 資料庫定義 | 資料表、VIEW、索引，依編號順序執行 | sql/ddl/ |

分工：`sql/ddl/`、`sql/procedures/`、`crawler/`、`backtest/` 由使用者撰寫；`app/` 由 Claude 撰寫，且只呼叫 VIEW 與預存程序。

### 2.2 資料表

| 類別 | 資料表 | 用途 |
|---|---|---|
| 市場資料 | stocks | 代號、名稱、產業、市場別、證券類別（股票／ETF／債券ETF）、上市狀態。下市股票不刪，避免回測存活者偏差 |
| 市場資料 | daily_prices | PK（代號, 日期）；開高低收量額，使用 DECIMAL |
| 市場資料 | daily_valuations | PK（代號, 日期）；本益比、殖利率、股價淨值比 |
| 市場資料 | corporate_actions | 除權息：代號、除權息日、現金股利、配股率、發放日 |
| 市場資料 | trading_calendar | 日期、是否交易日；來源為 TWSE 休市日公告，用來計算 T+2 |
| 市場資料 | tax_rates | 證券類別對應證交稅率：股票 0.3%、ETF 0.1%、債券ETF 依公告 |
| 快取／批次 | crawl_status | PK（資料集, 日期）；狀態 SUCCESS／NO_DATA（休市）／FAILED。只有 FAILED 會重試，`--force` 才重抓 |
| 快取／批次 | backfill_requests | 使用者要求補抓的區間與狀態 |
| 快取／批次 | etl_log | 每次批次的日期、筆數、成功失敗、錯誤訊息 |
| 帳務 | account | 初始資金、手續費率 0.1425%、折扣、最低手續費 20 元 |
| 帳務 | watchlist | 自選清單 |
| 帳務 | orders | 委託；狀態 PENDING 轉為 FILLED／REJECTED／CANCELLED／EXPIRED；委託只在下一個交易日有效 |
| 帳務 | trades | 成交明細，只新增 |
| 帳務 | cash_ledger | 現金流水帳，只新增，錯誤用沖正。分錄類型：買進應付、賣出應收、交割、圈存、圈存釋放、手續費月退、現金股利、二代健保補充保費 |
| 帳務 | positions | 持股、總成本、平均成本，與成交在同一交易內更新 |
| 帳務 | nav_snapshots | 每日淨值 |

原始回應另存於 `data/raw/{資料集}/{YYYYMMDD}.json`（已列入 gitignore），檔案存在就不再請求。

### 2.3 VIEW

| VIEW | 用途 |
|---|---|
| vw_stock_latest_metrics | 最新收盤、5／20 日均線、報酬率、估值；資料不足 20 天時均線為 NULL |
| vw_portfolio | 持倉加現價，得出市值、未實現損益、累計股利 |
| vw_realized_pnl | 已實現損益 |
| vw_cash_balance | 交割餘額、應收、應付、圈存、可用額度 |

### 2.4 預存程序

| 預存程序 | 參數 | 行為 |
|---|---|---|
| usp_screen_stocks | @max_pe, @min_yield, @above_ma20, @min_avg_volume, … | 參數為 NULL 代表不篩該條件，寫法 `(@p IS NULL OR col <= @p)`，並加 `OPTION (RECOMPILE)` |
| usp_place_order | @stock_id, @side, @lots | 只接受整張（1 張 = 1000 股）。檢查股票存在、股數合法。賣單檢查「當天開盤前已持有股數減未成交賣單」，不允許當沖。買單以「今日收盤 × 1.1 + 預估手續費」圈存資金，可用額度不足則拒絕 |
| usp_cancel_order | @order_id | 取消 PENDING 委託並釋放圈存 |
| usp_fill_pending_orders | @trade_date | 以 @trade_date 開盤價依委託時間逐筆成交（WHILE 迴圈，每筆一個交易）。單筆失敗只把該筆標為 REJECTED 並寫入原因。無開盤價（停牌）則標為 EXPIRED 並釋放圈存。成交後釋放圈存、記應付或應收（交割日為 T+2 營業日，查 trading_calendar）、更新 positions |
| usp_settle | @date | 把交割日為 @date 的應收應付轉為已交割 |
| usp_process_corporate_actions | @date | 權利以除權息前一交易日收盤持股判定。現金股利於除息日記應收、發放日入帳，單次 ≥ 20,000 元扣二代健保 2.11%。股票股利於除權日增加股數，總成本不變（平均成本下降） |
| usp_monthly_fee_rebate | @month | 手續費月退：成交時收全額 0.1425%，每月初依折扣把差額退回 cash_ledger |
| usp_take_nav_snapshot | @trade_date | 淨值 = 現金 + Σ(持股 × 收盤)；同日重跑用 MERGE 覆蓋 |
| usp_reconcile_positions | 無 | 以 trades 依序重算移動平均成本（遞迴 CTE 或迴圈），以 FULL OUTER JOIN 比對 positions 並回報差異 |

### 2.5 金額規則（台灣券商顯示邏輯，移動平均成本）

- 手續費 = max(最低手續費, floor(成交價 × 股數 × 0.1425%))。成交時收全額，折扣於月退。
- 賣出另收證交稅 = floor(價金 × 稅率)。
- 買進：總成本 += 價金 + 手續費；平均成本 = 總成本 ÷ 股數。
- 賣出：已實現損益 = (價金 − 手續費 − 稅) − 平均成本 × 股數；平均成本不變。
- 未實現損益 = 市值 − 預估賣出手續費 − 預估證交稅 − 總成本。
- 現金股利不扣成本，另顯示累計股利與含息損益。
- 可用額度 = 交割帳戶餘額 + 應收 − 應付 − 圈存。

---

## 3. 類別設計

### TwseClient

**職責：** 向 TWSE 取得原始資料。先查 raw 快取檔，命中就不發請求。`stat` 非 OK 視為非交易日，回傳空清單。網路錯誤重試 3 次，間隔逐次加長。請求間隔至少 3 秒。

**介面：**
```python
class TwseClient:
    def fetch_daily_quotes(self, trade_date: date) -> list[dict]:
        """取得指定日期的上市證券每日行情；非交易日回傳空清單。"""
        ...

    def fetch_daily_valuations(self, trade_date: date) -> list[dict]:
        """取得指定日期的本益比、殖利率、股價淨值比。"""
        ...

    def fetch_corporate_actions(self, start: date, end: date) -> list[dict]:
        """取得區間內的除權息資料。"""
        ...

    def fetch_holidays(self, year: int) -> list[dict]:
        """取得指定年度的休市日。"""
        ...
```

**依賴：**
- 輸入來源：TWSE 公開端點、`data/raw/` 快取檔
- 輸出去向：run_daily、run_backfill（再交給 cleaners 與 StockRepository）

### cleaners

**職責：** 把 TWSE 原始字串轉成可寫入資料庫的型別。

**介面：**
```python
def parse_number(raw: str) -> Decimal | None:
    """"1,234.5" 轉為 Decimal；"--" 轉為 None。"""
    ...

def parse_roc_date(raw: str) -> date:
    """民國日期轉西元日期，例如 "115/10/20" 轉為 2026-10-20。"""
    ...
```

**依賴：**
- 輸入來源：TwseClient 回傳的原始欄位字串
- 輸出去向：StockRepository 寫入前的清理步驟

### StockRepository

**職責：** 批次寫入 `#staging` 再以單一 MERGE 寫入正式表，同一天的寫入在同一個交易內。只使用參數化查詢。同時維護 crawl_status 與 etl_log，並負責呼叫每日預存程序。

**介面：**
```python
class StockRepository:
    def upsert_stocks(self, rows: list[dict]) -> int: ...
    def upsert_daily_prices(self, rows: list[dict]) -> int: ...
    def upsert_valuations(self, rows: list[dict]) -> int: ...
    def upsert_corporate_actions(self, rows: list[dict]) -> int: ...
    def upsert_calendar(self, rows: list[dict]) -> int:
        """回傳寫入（新增或更新）的筆數。"""
        ...

    def get_crawl_status(self, dataset: str, start: date, end: date) -> dict[date, str]:
        """回傳區間內每個已記錄日期的狀態。"""
        ...

    def mark_crawl_status(self, dataset: str, trade_date: date, status: str) -> None: ...

    def run_daily_procedures(self, trade_date: date) -> None:
        """依序執行每日預存程序。"""
        ...

    def write_etl_log(self, trade_date: date, status: str, rows: int, error: str | None) -> None: ...
```

**依賴：**
- 輸入來源：cleaners 清理後的資料列
- 輸出去向：SQL Server 資料表與預存程序

### run_daily

**職責：** 串接每日批次。非交易日記為 SKIPPED，不執行成交。由 macOS launchd 每天 18:00 排程。

**介面：**
```python
def run(trade_date: date) -> None:
    """依序：抓並寫入當日資料、結算、除權息、成交、淨值快照、（月初）手續費月退、寫 etl_log。"""
    ...
```

**依賴：**
- 輸入來源：launchd 排程、命令列參數
- 輸出去向：StockRepository、TwseClient

### run_backfill

**職責：** 處理 backfill_requests。只抓 crawl_status 中沒有 SUCCESS 或 NO_DATA 的日期；`force` 為真時全部重抓。

**介面：**
```python
def run(start: date, end: date, force: bool = False) -> None: ...
```

**依賴：**
- 輸入來源：backfill_requests、app 以 subprocess 啟動的 CLI
- 輸出去向：StockRepository、TwseClient、crawl_status

### db（app/db.py）

**職責：** 面板的唯一資料庫入口。連線字串從 `.env` 讀取。

**介面：**
```python
def query(sql: str, params: dict | None = None) -> pd.DataFrame:
    """查詢 VIEW，回傳 DataFrame。"""
    ...

def execute_procedure(name: str, params: dict) -> pd.DataFrame:
    """呼叫預存程序，回傳其結果集。"""
    ...
```

**依賴：**
- 輸入來源：各面板頁面、`.env`
- 輸出去向：SQL Server 的 VIEW 與預存程序

### 面板頁面（app/pages/）

**職責：** 顯示與接收操作，不寫商業邏輯的 SQL。

| 頁面 | 內容 |
|---|---|
| 首次設定 | crawl_status 為空時顯示，詢問補抓範圍 |
| 選股 | 輸入條件，呼叫 usp_screen_stocks |
| 個股 | plotly K 線加均線 |
| 下單 | 呼叫 usp_place_order、usp_cancel_order |
| 持倉 | vw_portfolio、vw_cash_balance，淨值曲線用 st.line_chart |
| 回測結果 | 顯示 BacktestResult |

市場資料使用 `st.cache_data(ttl)`；持倉與委託不快取。

### Backtester

**職責：** 最簡版回測：一組條件、每月調倉，指標為總報酬、最大回撤，並對比 0050。使用暫時帳戶重複呼叫預存程序，不動真實模擬帳戶。

**介面：**
```python
class Backtester:
    def run(self, start: date, end: date, screen_params: dict, rebalance: str) -> BacktestResult:
        """回傳回測結果（總報酬、最大回撤、與 0050 的對比）。"""
        ...
```

**依賴：**
- 輸入來源：呼叫端傳入的區間與選股條件
- 輸出去向：app 的回測結果頁（以結果儲存或命令列輸出傳遞，不 import 彼此）

---

## 4. 資料流

### 4.1 每日批次

```
launchd（每天 18:00）
  → run_daily.run(trade_date)
    → 非交易日：寫 etl_log 為 SKIPPED，結束（不跑成交）
    → TwseClient.fetch_*（先查 raw 快取，再請求，間隔 >= 3 秒）
    → cleaners 清理 → StockRepository.upsert_*（#staging + 單一 MERGE）
    → StockRepository.mark_crawl_status(dataset, trade_date, SUCCESS / NO_DATA / FAILED)
    → usp_settle(trade_date)
    → usp_process_corporate_actions(trade_date)
    → usp_fill_pending_orders(trade_date)
    → usp_take_nav_snapshot(trade_date)
    → （月初）usp_monthly_fee_rebate(month)
    → StockRepository.write_etl_log(...)
```

### 4.2 首次啟動與補抓

```
使用者開啟面板
  → app 檢查 crawl_status 是否為空
    → 為空：顯示首次設定頁（預設 1 週；選項 1 週／1 個月／1 年／3 年／自訂起日）
      提示：回測至少需要 1 年資料，3 年約需 2 小時
  → 送出：寫入 backfill_requests
  → app 以 subprocess 在背景啟動 crawler/run_backfill.py（不 import）
  → run_backfill.run(start, end, force) 只抓缺漏日期
  → 首次設定頁從 crawl_status 顯示進度
```

之後使用者可隨時補抓更早的資料；已爬過的日期不重爬。

### 4.3 下單到持倉

```
使用者（下單頁）
  → db.execute_procedure("usp_place_order", {stock_id, side, lots})
    → 檢查股票、股數；賣單檢查可賣股數；買單檢查可用額度並圈存
  → 回傳委託結果（PENDING 或拒絕原因）
隔日批次
  → usp_fill_pending_orders(trade_date)：以開盤價成交 → 釋放圈存 → 記應付／應收 → 更新 positions
  → usp_settle：T+2 轉為已交割
  → 持倉頁 → db.query(vw_portfolio, vw_cash_balance)
```

### 4.4 回測

```
回測結果頁 / 命令列
  → Backtester.run(start, end, screen_params, rebalance)
    → 建立暫時帳戶
    → 每個調倉日：呼叫 usp_screen_stocks → 下單 → 成交 → 淨值快照
    → 計算總報酬、最大回撤，對比 0050
  → 回傳 BacktestResult
```

---

## 5. 依賴關係圖

```
app/
  ├── 依賴 sql/ 的 VIEW（vw_stock_latest_metrics、vw_portfolio、vw_realized_pnl、vw_cash_balance）
  ├── 依賴 sql/ 的預存程序（usp_screen_stocks、usp_place_order、usp_cancel_order）
  ├── 依賴 backfill_requests、crawl_status（讀寫，首次設定頁）
  └── 以 subprocess 呼叫 crawler/run_backfill.py（不 import）

crawler/
  ├── 依賴 TWSE 外部端點（行情、估值、除權息、休市日）
  ├── 依賴 sql/ 的資料表（寫入）
  └── 依賴 sql/ 的預存程序（usp_settle、usp_process_corporate_actions、
      usp_fill_pending_orders、usp_take_nav_snapshot、usp_monthly_fee_rebate）

backtest/
  ├── 依賴 sql/ 的預存程序（選股、下單、成交、淨值）
  └── 依賴 sql/ 的資料表（歷史資料、暫時帳戶）

sql/procedures/
  └── 依賴 sql/ddl/ 的資料表與 VIEW

app/、crawler/、backtest/ 彼此不互相 import
```

---

## 6. 邊緣案例與錯誤處理

| 情境 | 處理方式 |
|---|---|
| 非交易日或休市 | TwseClient 回傳空清單，crawl_status 記 NO_DATA，etl_log 記 SKIPPED，不執行成交 |
| 停牌無開盤價 | usp_fill_pending_orders 將委託標為 EXPIRED，並釋放圈存 |
| 可用額度不足 | usp_place_order 拒絕下單 |
| 成交價金高於圈存 | 一般股票漲停 10%，開盤價不會超出「收盤 × 1.1」。但新上市前 5 個交易日、含國外成分股的 ETF 沒有漲跌幅限制，仍可能超出：成交時重新檢查「可用額度 + 該筆圈存」，不足就標為 REJECTED 並釋放圈存 |
| 賣單股數超過可賣股數 | usp_place_order 拒絕（可賣股數 = 當天開盤前持有股數減未成交賣單），同時達成不允許當沖 |
| 重複執行同一天批次 | MERGE 與 crawl_status 保證冪等；usp_take_nav_snapshot 以 MERGE 覆蓋 |
| 爬蟲中途失敗 | 整日交易 rollback，crawl_status 記 FAILED；下次只重試 FAILED，`--force` 才全部重抓 |
| 單筆成交失敗 | 只把該筆標為 REJECTED 並寫入原因，不影響其他委託 |
| 除權息日前一天才買進 | 仍有權利：權利以除權息前一交易日收盤時的持股判定，不看是否已完成 T+2 交割 |
| 單次現金股利 ≥ 20,000 元 | 扣二代健保補充保費 2.11% |
| 均線資料不足 20 天 | vw_stock_latest_metrics 的均線回傳 NULL |
| 網路錯誤 | TwseClient 重試 3 次，間隔逐次加長 |
| TWSE 端點改版 | 以官網為準，實作時確認 |
| crawl_status 為空 | 面板顯示首次設定頁 |

---

## 7. 測試涵蓋（對應 Unit Test）

專案檔未定義〈測試〉，以下為建議測試案例。測試檔案位置待專案確定測試目錄後調整，此處暫以 `tests/` 表示。

| 測試案例 | 測試檔案 | 說明 |
|---|---|---|
| test_parse_number_thousand_separator | tests/test_cleaners.py | "1,234.5" 轉為 Decimal("1234.5") |
| test_parse_number_dash_returns_none | tests/test_cleaners.py | "--" 回傳 None |
| test_parse_roc_date | tests/test_cleaners.py | "115/10/20" 轉為 2026-10-20 |
| test_fetch_returns_empty_when_stat_not_ok | tests/test_twse_client.py | stat 非 OK 時回傳空清單 |
| test_fetch_uses_raw_cache | tests/test_twse_client.py | raw 檔存在時不發請求 |
| test_fetch_retries_three_times | tests/test_twse_client.py | 網路錯誤重試 3 次後才拋出 |
| test_upsert_is_idempotent | tests/test_repository.py | 同一批資料寫入兩次，筆數不重複 |
| test_get_crawl_status | tests/test_repository.py | 回傳區間內的日期與狀態對照 |
| test_run_daily_skips_non_trading_day | tests/test_run_daily.py | 非交易日記 SKIPPED，不呼叫成交 |
| test_run_backfill_skips_done_dates | tests/test_run_backfill.py | 已有 SUCCESS／NO_DATA 的日期不重抓，force 時重抓 |
| test_place_order_rejects_insufficient_funds | SQL 整合測試 | 可用額度不足時拒絕 |
| test_place_order_rejects_day_trade_sell | SQL 整合測試 | 賣單超過可賣股數時拒絕 |
| test_fill_order_expired_when_no_open_price | SQL 整合測試 | 停牌時 EXPIRED 並釋放圈存 |
| test_fee_and_tax_floor | SQL 整合測試 | 手續費與證交稅取 floor，最低手續費 20 元 |
| test_moving_average_cost | SQL 整合測試 | 買進後平均成本正確；賣出後平均成本不變 |
| test_settlement_t_plus_2_skips_holidays | SQL 整合測試 | 交割日跳過休市日 |
| test_dividend_nhi_threshold | SQL 整合測試 | 單次 ≥ 20,000 元才扣 2.11% |
| test_stock_dividend_keeps_total_cost | SQL 整合測試 | 配股後股數增加、總成本不變 |
| test_reconcile_positions_detects_diff | SQL 整合測試 | positions 被改動時回報差異 |
| test_ma_null_when_less_than_20_days | SQL 整合測試 | 資料不足 20 天時均線為 NULL |

---

## 8. 待決定事項

- [ ] 證交所資料授權：使用者自行確認（目前已決定不附資料）
- [ ] TWSE 各資料集的最早可查日期，實作時確認
- [ ] 除權除息預告表與休市日的實際端點，實作時確認
- [ ] 專案測試目錄與 SQL 整合測試的執行方式（專案檔未定義〈測試〉）
- [ ] BacktestResult 的欄位與回測結果傳遞給回測結果頁的方式

### 刻意簡化（README 要寫明，之後可擴充）

- 不允許當沖（同日買賣同一檔）。
- 只交易整張，不支援零股。
- 委託只在下一交易日有效。
- 用圈存模擬「不會違約交割」的帳戶（實務多用下單額度）。
- 單一帳戶。

### Milestone 對照（21 天，每天 2 小時，每個結束打 tag 並更新 README 截圖）

| Milestone | 天數 | 內容 | Tag |
|---|---|---|---|
| M1 資料庫上線 | Day 1–7 | 資料表、爬蟲、快取、補抓、etl_log、資料品質檢查 | v0.1 |
| M2 選股面板 | Day 8–11 | 視窗函數、VIEW、usp_screen_stocks、索引調校（使用者）；選股頁、個股頁（Claude） | v0.2 |
| M3 模擬交易與持倉 | Day 12–19 | 委託、成交、T+2 交割、除權息、月退、淨值、對帳 SP（使用者）；首次設定頁、下單頁、持倉頁（Claude） | v0.3 |
| M4 回測與收尾 | Day 20–21 | 最簡版回測（使用者）；回測結果頁、README（Claude） | v0.4 |
