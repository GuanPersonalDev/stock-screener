# sql-stock-screener

兩週 SQL 學習專案：爬取台股每日行情與估值資料，寫入 MS SQL Server，
以視窗函數與預存程序計算選股條件，最後用 Streamlit 做成網頁選股面板。

> 進行中。學習計畫見 [docs/learning-map.md](docs/learning-map.md)。

## 架構

```
TWSE 公開資料 ──► crawler/（Python 爬蟲與清理）
                      │  參數化查詢、交易、upsert
                      ▼
               SQL Server：StockLab
               ├─ 資料表   sql/ddl/
               ├─ VIEW     sql/ddl/
               └─ 預存程序 sql/procedures/
                      │
                      ▼
               app/（Streamlit 選股面板）
```

## 目錄

| 路徑 | 內容 |
|---|---|
| `docs/` | 學習地圖、環境建置、銀行 SQL 需求對照、ER 圖 |
| `sql/ddl/` | 建表、VIEW、索引，依編號順序執行 |
| `sql/queries/` | 每日練習的查詢 |
| `sql/procedures/` | 預存程序 |
| `crawler/` | 爬蟲與寫入資料庫 |
| `app/` | Streamlit 面板 |
| `notes/` | 每日學習筆記 |

## 啟動

見 [docs/setup.md](docs/setup.md)。
