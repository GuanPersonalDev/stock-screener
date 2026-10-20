# 銀行職缺常見的 SQL 需求

銀行的資料系統以 MS SQL Server 與 Oracle 為主，工作內容多半落在報表、對帳、批次與資料品質。
下表把常見需求對應到這個專案的練習日，面試前用來自測。

## 實務需求對照

| 實務需求 | 銀行情境 | 關鍵語法 | 在本專案的練習 |
|---|---|---|---|
| 報表彙總 | 分行、產品、月份的交易量與餘額統計 | `GROUP BY`、`HAVING`、`CASE` | Day 2 |
| 對帳與差異比對 | 核心系統與外部檔案逐筆比對 | `LEFT JOIN … IS NULL`、`NOT EXISTS`、`EXCEPT` | Day 7、Day 19 |
| 取最新狀態 | 每位客戶最新一筆的評等、餘額 | `ROW_NUMBER() OVER (PARTITION BY …)` | Day 8 |
| 時間序列計算 | 日均餘額、累計交易、與前期比較 | `LAG`、`SUM() OVER`、視窗框架 | Day 8–9 |
| 批次匯入 | 每日夜間批次將檔案寫進資料庫 | 參數化查詢、`MERGE`、交易 | Day 5–6 |
| 預存程序 | 報表、批次邏輯、權限控管 | `CREATE PROCEDURE`、`TRY … CATCH` | Day 10、Day 14–18 |
| 效能調校 | 大表查詢太慢 | 索引、執行計畫、SARGable | Day 11 |
| 資料品質 | 重複、缺漏、異常值檢查 | `GROUP BY … HAVING COUNT(*) > 1` | Day 7 |
| 批次紀錄與稽核 | 每次批次執行留紀錄 | log 表設計 | Day 6 |
| 金額精確度 | 利息、餘額計算 | `DECIMAL`，不用 `FLOAT` | Day 2 |
| 帳務設計 | 只新增的流水帳、沖正、圈存、T+2 交割 | 交易、狀態欄位、`CHECK` | Day 12–16 |

## 之後可延伸（這次不做）

- **資料倉儲**：事實表與維度表（star schema）、緩慢變動維度（SCD Type 2）
- **交易隔離等級**：`READ COMMITTED`、`SNAPSHOT`、死結（deadlock）
- **權限**：`GRANT`／`REVOKE`、角色、只開 VIEW 與預存程序給應用程式
- **Oracle 語法差異**：`ROWNUM`、`NVL`、`MERGE` 寫法、序列（sequence）

## 面試題自測

每題先自己在 `StockLab` 寫出來，再對照筆記。

1. 找出每個產業收盤價第二高的股票（同價怎麼處理？）
2. 找出連續 3 天上漲的股票
3. 找出 `daily_prices` 裡重複的資料，並只保留一筆刪除其餘
4. 計算每檔股票的累計報酬率
5. `WHERE` 與 `HAVING` 的差別
6. `INNER JOIN` 與 `LEFT JOIN` 的差別；LEFT JOIN 的條件寫在 `ON` 與 `WHERE` 有什麼不同
7. `NOT IN` 遇到 NULL 的陷阱
8. `DELETE`、`TRUNCATE`、`DROP` 的差別
9. 叢集索引與非叢集索引的差別；一張表可以有幾個叢集索引
10. 什麼是 SQL Injection，怎麼防
11. 交易的 ACID 是什麼
12. 為什麼金額不能用 `FLOAT`
