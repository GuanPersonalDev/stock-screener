# Day 5｜寫入資料庫：參數化、MERGE、交易

日期：2026-11-04 ～ 2026-11-11　對應 Issue：#5

## 做了什麼

1. 用 `uv add pymssql python-dotenv` 加入資料庫驅動與 `.env` 讀取
2. 寫 `crawler/database_define.py`，集中表名、欄位名與 CHECK 約束的值
3. 寫 `crawler/repository.py` 的 `StockRepository`
4. 寫 `tests/test_repository.py`，連 Docker 裡的 SQL Server 驗收

| 檔案 | 內容 |
|---|---|
| `crawler/repository.py` | `StockRepository`：`#staging` + `MERGE` 的批次 upsert、`crawl_status`、`etl_log`、`transaction()` |
| `crawler/database_define.py` | 表名、欄位名、狀態值常數；`TwseClient` 的 dict key 改用這裡的常數 |
| `crawler/cleaners.py` | 新增 `classify_security_type`：`00` 開頭為 ETF，其中 `B` 結尾為債券 ETF |
| `tests/test_repository.py` | 9 個整合測試，連不上資料庫就 skip |

## StockRepository 的職責

- 爬蟲寫進資料庫的唯一入口：資料表的讀寫都在這裡，其他層看不到 SQL。
- 不做：發 HTTP 請求（TwseClient）、字串轉型（cleaners）、決定流程與 commit 時機（run_daily）、帳務邏輯（預存程序）。
- 判斷標準：跟資料表打交道的放進來；「要不要做、什麼時候做」的判斷不放。

## 參數化查詢

- 值一律用佔位符傳入，pymssql 的佔位符是 `%s`，不是 `?`。
- 表名、欄位名不能參數化（參數只能代表值）。這裡用 f-string 或 `.format()` 組的只有 `database_define` 裡寫死的常數，不含任何外部輸入，所以安全。

```python
cur.execute("SELECT ... WHERE dataset = %s AND trade_date BETWEEN %s AND %s", (dataset, start, end))
cur.executemany("INSERT INTO #staging (...) VALUES (%s, %s, ...)", tuples)
```

## #staging + MERGE

每個 upsert 都是同一個流程，抽成私有方法 `_merge_via_staging`：

1. `DROP TABLE IF EXISTS #staging;` 再 `SELECT TOP 0 {columns} INTO #staging FROM {table};`
2. `executemany` 把資料寫進 `#staging`
3. 一個 `MERGE` 合併進正式表
4. 回傳 `cur.rowcount`（新增加更新的筆數）

- `#` 開頭是區域暫存表，只有這條連線看得到，連線關閉才消失，所以每次都要先 DROP。
- upsert = update + insert：有就更新、沒有就新增。SQL Server 用 `MERGE`；PostgreSQL 是 `ON CONFLICT`，MySQL 是 `ON DUPLICATE KEY UPDATE`。

### MERGE 的寫法

```sql
MERGE dbo.daily_prices AS t
USING #staging AS s
   ON t.stock_id = s.stock_id AND t.trade_date = s.trade_date
WHEN MATCHED AND EXISTS (SELECT s.<欄位> EXCEPT SELECT t.<欄位>)
    THEN UPDATE SET open_price = s.open_price, ...
WHEN NOT MATCHED BY TARGET
    THEN INSERT (...) VALUES (s....);
```

- 結尾一定要有 `;`。
- `ON` 只放配對鍵，篩選條件放 `WHEN ... AND`。
- 不寫 `WHEN NOT MATCHED BY SOURCE THEN DELETE`：`#staging` 只有一天的資料，寫了會刪光其他日期。
- `UPDATE SET` 不寫表名，主鍵不放進 SET；沒寫進 SET 的欄位保留原值，所以 stocks 不會蓋掉 `industry`、`listing_status`。
- 來源有兩列對到目標同一列時 MERGE 會報錯（`attempted to UPDATE or DELETE the same row more than once`）。
- 單筆的 upsert（`crawl_status`）來源用 `USING (VALUES (%s, %s, %s)) AS s(dataset, trade_date, status)`，括號只包住 `VALUES (...)`。

### 為什麼用 EXISTS + EXCEPT 判斷有沒有變

- `t.col <> s.col` 遇到 NULL 結果是 UNKNOWN，會被當成 FALSE：舊值 NULL、新值 11 的那一列不會更新。
- `EXCEPT` 比較時把 NULL 與 NULL 視為相同，一句就處理好所有欄位的 NULL。
- 沒變的列不 UPDATE，重跑同一天時 `rowcount` 是 0，冪等看得出來。
- SET 的欄位要和 EXCEPT 比較的欄位一致。

## 交易

- pymssql 的 `autocommit=False` 時，第一句 SQL 自動開始交易；`commit()` 讓修改永久生效、其他連線看得到；`rollback()` 撤回到交易開始前；沒 commit 就關閉連線等於 rollback。
- 寫入方法全部不 commit，由呼叫端決定交易邊界：

```python
@contextmanager
def transaction(self):
    try:
        yield
        self._conn.commit()
    except Exception:
        self._conn.rollback()
        raise
```

- `raise` 不可省略，否則失敗會被吞掉，呼叫端以為成功。
- Day 6 的 `run_daily`：HTTP 請求放在交易外；stocks → prices → valuations → `crawl_status` SUCCESS → `etl_log` 放在同一個交易；失敗時 rollback 後另開一個交易寫 FAILED 紀錄，才不會跟著被撤回。
- 寫入順序是 stocks 先，因為 prices、valuations 都有 FK 指向 stocks。

## Python 的細節

- `uv add` 會更新 `pyproject.toml`、`uv.lock` 並裝進 `.venv`；用 `uv run` 執行就會用 `.venv`，VS Code 要選 `.venv/bin/python` 才不會畫紅線。
- `import pymssql`；`python-dotenv` 的 import 名稱是 `dotenv`。
- `load_dotenv()` 把 `.env` 讀進 `os.environ`；用 `os.environ["KEY"]` 而不是 `.get()`，缺設定時立刻 `KeyError`。
- 模組最上層 import 的名稱是全域名稱，函式本體在呼叫時才依 LEGB 查找，所以方法裡用得到。
- 型別註記在定義時就計算，類別本體裡還沒有類別名稱，所以回傳型別寫 `Self`（3.11 以後）或加引號。
- f-string 在執行到那一行時就填值；要當範本之後再填，用普通字串加 `.format()`。
- `_` 開頭的方法是內部實作的慣例，不是強制限制。

## 踩到的坑

- `MERGE` 的 `EXISTS (` 少了收尾的 `)`，結尾又多一個 `)`；`USING (VALUES (...) AS s(...))` 括號包錯範圍。
- `SELECT TOP 0 * INTO #staging` 會複製 NOT NULL 但不複製 DEFAULT：`stocks.listing_status` 是 `NOT NULL DEFAULT 'LISTED'`，INSERT 沒寫它就變成 NULL 而失敗。改成只選要寫的欄位 `SELECT TOP 0 {columns} INTO`，DEFAULT 留給正式表在 MERGE 的 INSERT 時補上。原則：中間層的形狀跟著「這一步需要什麼」，不照抄目的地。
- 修正時把 `CREATE_STAGING_SQL` 寫成 f-string，import 時就 `NameError: name 'columns' is not defined`；同時漏掉 `cur.execute(merge_sql)`，資料只進了 `#staging`。
- Docker 沒開時 pymssql 預設等約 60 秒才放棄，9 個整合測試 skip 花了 81 秒；可以在 `connect` 加 `login_timeout`。

## 之後要處理的事

- 行情裡有 14 檔 ETN（`02` 開頭，例如 `020000`、`02001L`），目前被 `classify_security_type` 歸為 `STOCK`。CHECK 約束擋不下來，但證交稅率不同，做 `tax_rates` 前要決定 ETN 的分類。
- `HttpFetcher` 的快取路徑 `Path("data/raw")` 相對於執行目錄，Day 6 用 launchd 排程前要改成以 `Path(__file__)` 為基準。

## 驗收

- [x] 只用參數化查詢，不拼接 SQL 字串（字串組合只用於 `database_define` 的表名與欄位名）
- [x] 同一天寫入兩次，資料不重複（2026-10-29 實際資料：第一次 stocks 1388、prices 1388、valuations 1087，第二次三者都回傳 0）
- [x] 中途故意丟例外，資料庫不會留下半天的資料（整合測試 `test_exception_in_transaction_rolls_back_all_writes`；實際資料 rollback 後五張表皆 0 筆）
- [x] crawl_status 與 etl_log 正確寫入（`get_crawl_status` 回傳 `{date(2026, 10, 29): 'SUCCESS'}`，key 為 `datetime.date`）
- [x] `uv run pytest -q`：26 passed
