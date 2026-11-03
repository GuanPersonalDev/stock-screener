# Day 4｜爬蟲：TwseClient 與資料清理

日期：2026-10-30 ～ 2026-11-03　對應 Issue：#4

## 做了什麼

1. 用瀏覽器與實際請求確認證交所兩個端點的 JSON 結構
2. 寫 `crawler/cleaners.py` 的 `parse_number`、`parse_roc_date`，並用 pytest 測試
3. 把爬蟲拆成三個類別，更新技術文件 §2.1 與 §3 後再實作
4. 實際抓 2026-10-29（交易日）與 2026-11-01（星期日）驗收

| 檔案 | 內容 |
|---|---|
| `crawler/cleaners.py` | 單一欄位字串轉成 `Decimal`、`date` |
| `crawler/http_fetcher.py` | `HttpFetcher`：限速、重試、raw 快取，不認識證交所 |
| `crawler/config.toml` | 資料集 key 對應的 url 與固定查詢參數 |
| `crawler/crawler_config.py` | `CrawlerConfig`：用 `tomllib` 讀設定檔，依 key 查詢 |
| `crawler/twse_client.py` | `TwseClient`：Facade，組合上面兩個，負責解析與呼叫 cleaners |
| `tests/test_*.py` | 17 個單元測試，全部不連網 |

這一天只有 Python 與爬蟲，沒有讀寫資料庫。資料只存在記憶體的 `list[dict]` 與 `data/raw/` 的 JSON 檔。寫入資料庫是 Day 5。

## 證交所的端點

| key | 端點 | 內容 |
|---|---|---|
| `daily_quotes` | `MI_INDEX?date=YYYYMMDD&type=ALLBUT0999&response=json` | 某一天全部證券的行情（不含權證、牛熊證），約 1388 筆 |
| `daily_valuations` | `BWIBBU_d?date=YYYYMMDD&selectType=ALL&response=json` | 某一天全部股票的本益比、殖利率、股價淨值比，約 1087 筆 |

- `STOCK_DAY` 要帶 `stockNo`，回傳的是單一個股整個月，不適合每天抓全市場。
- `BWIBBU_d` 的 `_d` 是依日期查全市場；`BWIBBU` 是依代號查單一個股整月。這些代號是證交所內部的報表名稱，沒有公開的縮寫說明。
- 網址的 `?` 之後是查詢參數，用 `&` 連接。用 requests 時放進 `params={...}`，不必自己組。

## 回應格式的陷阱

- 數字都是字串，有千分位逗號：`'29,745,814'`。
- 無資料的寫法不一致：行情沒有成交時開高低收是 `'--'`，估值沒有本益比時是單一個 `'-'`。`parse_number` 兩種都要轉成 `None`。
- `MI_INDEX` 的 `tables` 有 9 張表，前面是大盤指數與統計。個股表要用 `fields` 裡有沒有 `"證券代號"` 找，不寫死 `tables[8]`。欄位也用名稱對應位置，不寫死索引。
- 行情的 `漲跌(+/-)` 是一段 HTML（`<p style= color:green>-</p>`），資料表沒有這欄，直接不取。
- 估值的 `股利年度` 已經是 int；`財報年/季`（`'115/2'`）不是日期，不能丟給 `parse_roc_date`。
- 休市日回傳的是 JSON，`stat` 不是 `"OK"`。短時間連續請求被擋時，回傳的是 HTML 頁面「因為安全性考量，您所執行的頁面無法呈現」。兩者要分開處理：前者回傳空清單，後者算網路錯誤要重試。

## cleaners

- 純函式：一次處理一個值，不讀檔、不連網，所以最好測。
- 用 `Decimal` 不用 `float`，因為 `float` 無法精確表示 `0.1`，而資料庫欄位是 `DECIMAL(10,2)`。
- `Decimal` 不接受逗號，先 `.replace(",", "")`。
- 證交所明確標示的無資料（`--`、`-`、空字串）回傳 `None`；`'abc'` 這種意外格式讓 `Decimal` 丟例外，不吞掉。吞掉的話，證交所改版會變成資料庫裡悄悄多出來的 NULL。
- `parse_roc_date`：民國年加 1911，兩位數的民國年（`'99/01/05'` → 2010-01-05）也正確。

## 為什麼拆成三個類別

原本技術文件只有一個 `TwseClient`，同時負責 HTTP 與證交所的格式。拆開後：

| 類別 | 會變動的原因 |
|---|---|
| `HttpFetcher` | 限速、重試、快取策略改變。加入櫃買中心時可以直接重用 |
| `CrawlerConfig` | 證交所的網址或參數改變，只改 `config.toml` |
| `TwseClient` | 證交所的回應格式改變 |

- `HttpFetcher` 是被組合（composition）的工具，不是被繼承的父類別，所以不取名 `CrawlerBase`。
- 設定檔只放常數。每個資料集的解析方式不同（行情要找表、估值直接取 `data`），這是程式邏輯，不塞進設定檔。
- 對外同時提供 `fetch_raw(key, trade_date)` 與具名方法。具名方法回傳的欄位固定，IDE 能補完；只用字串 key 的話，打錯 key 要執行時才知道。
- `TwseClient` 的建構子接受 `fetcher`、`config`，測試時可以換成暫存目錄與 `min_interval=0`。
- `crawler/` 和 `app/` 不能互相 import。面板要補抓資料時寫 `backfill_requests` 或用 subprocess 啟動 `python -m crawler.run_backfill`，不直接呼叫 `TwseClient`。

## 快取、限速、重試

- 快取路徑是 `data/raw/{key}/{YYYYMMDD}.json`，例如 `data/raw/daily_quotes/20261029.json`。資料夾名稱是設定檔的 key，不是 `MI_INDEX`。
- 只快取 `stat` 為 `"OK"` 的回應。把 HTML 錯誤頁或休市回應存成快取，之後就會一直讀到壞資料。
- 回應裡的 `date` 和要求的日期不同時丟出 `ValueError`，避免把別天的資料存成這一天。
- 限速記錄上次真正發出請求的時間，用 `time.monotonic()`，不受系統時間調整影響。讀快取不算請求，不必等待。
- 重試也是請求，每次重試前一樣經過限速；重試間隔逐次加倍。全部失敗時用不帶參數的 `raise` 丟出最後一次的原始例外，Day 6 接到後記成 `FAILED`。
- `response.json()` 解析失敗丟的 `requests.JSONDecodeError` 繼承 `ValueError`，所以捕捉 `ValueError` 就能接到 HTML 封鎖頁。
- 快取檔用 `ensure_ascii=False` 寫入，中文保持可讀。

## Python 的細節

- requests 是通用的 HTTP 客戶端，不是爬蟲框架。證交所直接回 JSON，不需要 BeautifulSoup（解析 HTML）、Selenium（執行 JavaScript）或 Scrapy（大規模爬取）。
- `crawler/__init__.py` 讓 `crawler/` 成為 package。從 repo 根目錄用 `python -m crawler.xxx` 執行，`from crawler.cleaners import …` 才找得到。
- 有狀態的寫成類別（`TwseClient` 要記住上次請求時間與 session），純函式寫成模組函式（`cleaners`）。
- `f"{trade_date:%Y%m%d}"` 可以在 f-string 裡直接套用 strftime 格式。
- `CrawlerConfig` 的預設路徑用 `Path(__file__).parent / "config.toml"`，不論從哪個目錄執行都找得到。
- Python 3.11 之後內建 `tomllib`，讀 TOML 不必安裝套件；要用 `"rb"` 開檔。
- 套件用 `uv add requests` 安裝，會同時更新 `pyproject.toml` 與 `uv.lock`。

## 踩到的坑

- `parse_number` 第一版只處理 `'--'`，遇到估值的 `'-'` 丟出 `InvalidOperation`，整天的估值都會失敗。
- 實測時連續請求，第三次就拿到 HTML 封鎖頁，一度以為休市日回傳的是 HTML。之後隔一段時間單獨抓星期日，才確認休市日回傳的是 `stat` 非 OK 的 JSON。

## Day 5 要處理的事

- 行情裡除了股票、ETF、債券 ETF，還有 ETN 等其他證券。寫入 `stocks` 前要決定怎麼分類或篩選，否則會被 `CK_stocks_security_type` 擋下。
- 需要資料庫驅動（`docs/setup.md` 建議先用 `pymssql`）。

## 驗收

- [x] 非交易日回傳空清單，不丟例外（2026-11-01 實測回傳 `[]`，且沒有寫入快取）
- [x] 第二次抓同一天不會發出請求（第二次讀取 0.011 秒，另有單元測試）
- [x] 清理後的數字沒有逗號、沒有 `--`（2026-10-29 的 2475 筆資料檢查過）
- [x] TwseClient 能取得行情與估值資料（行情 1388 筆、估值 1087 筆）
- [x] 輸出的欄位與型別符合技術文件（key 用 DDL 欄位名，價格是 `Decimal`，股數與金額是 `int`）
- [x] raw 回應已快取（`data/raw/daily_quotes/`、`data/raw/daily_valuations/`）
