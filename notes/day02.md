# Day 2｜SELECT、資料型別、聚合

日期：2026-10-21　對應 Issue：#2

## 做了什麼

1. 在 `StockLab` 建練習表 `practice_stocks`，手動 `INSERT` 10 檔股票（4 個產業）
2. 寫 8 類查詢：價格區間、產業篩選、模糊搜尋、取前 3 名、各產業平均價、`CASE` 分價位、`HAVING`、`COUNT` 與 NULL
3. 多寫一題子查詢：列出「平均價大於 100 的產業」裡的所有股票
4. 比較 `FLOAT` 與 `DECIMAL` 計算 0.1 + 0.2 的結果

查詢全部放在 `sql/queries/day02_select.sql`。

## 資料型別

| 型別 | 用途 | 本次用在 |
|---|---|---|
| `VARCHAR(n)` | 只有英數字的字串 | `stock_id` |
| `NVARCHAR(n)` | 含中文的字串（Unicode），字面值要寫成 `N'…'` | `stock_name`、`industry` |
| `DECIMAL(p, s)` | 精確的十進位數，p 是總位數，s 是小數位數 | `close_price`、`dividend` |
| `DATE` | 只有日期，不含時間 | `listed_date` |
| `INT` | 整數 | 本次沒用到 |

- 中文字串沒加 N，存進去會變成 `???`。
- `NULL` 不加引號；寫成 `'NULL'` 會變成四個字母的字串。
- `DROP TABLE IF EXISTS` 讓整份檔案可以重複執行，只用在練習表。

## 查詢語法整理

| 語法 | 意義 | 例子 |
|---|---|---|
| `BETWEEN a AND b` | 介於 a 與 b，包含兩端 | 價格 50～200，共 6 檔 |
| `IN (…)` | 符合清單中任一值 | `industry IN (N'半導體', N'金融')` |
| `LIKE N'%金%'` | `%` 是任意長度字元，`_` 是剛好一個字元 | 富邦金、國泰金、中信金 |
| `TOP n … ORDER BY` | T-SQL 取前 n 筆，其他資料庫用 `LIMIT`；一定要搭配排序 | 聯發科、台積電、廣達 |
| `GROUP BY` | 相同值的列合併成一組，每組輸出一列 | 依產業分組 |
| `COUNT`、`AVG`、`SUM` | 聚合函數，在每組內各自計算 | 各產業檔數與平均價 |
| `HAVING` | 篩選分組後的結果，條件可用聚合函數 | 平均價 > 100 的產業 |
| `CASE WHEN … THEN … ELSE … END` | 由上往下判斷，第一個成立就停；省略 `ELSE` 得到 NULL | 高價股、中價股、低價股 |
| `IS NULL` | 判斷 NULL 唯一正確的寫法，`= NULL` 永遠查不到 | 聯電、緯創沒有股利資料 |

- 有 `GROUP BY` 時，`SELECT` 只能放分組欄位或聚合函數。
- `AVG` 對 `DECIMAL` 取平均，結果會顯示到小數 6 位（例如 `63.333333`）。

各產業平均價（查詢 5）：

| industry | stock_count | avg_price |
|---|---|---|
| 半導體 | 3 | 750.000000 |
| 電子代工 | 3 | 190.000000 |
| 通信網路 | 1 | 125.000000 |
| 金融 | 3 | 63.333333 |

## 邏輯執行順序

```
FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY
```

- `SELECT` 取的別名，只有排在它之後的 `ORDER BY` 能用。
- `HAVING` 要寫 `AVG(close_price) > 100`，不能寫 `avg_price > 100`。

## 子查詢

```sql
WHERE industry IN (
    SELECT industry
    FROM practice_stocks
    GROUP BY industry
    HAVING AVG(close_price) > 100
);
```

- 內層先算出符合條件的產業清單（半導體、電子代工、通信網路），外層再用 `IN` 篩出這些產業的股票，共 7 檔。
- `HAVING` 只能回答「哪些組符合」，要拿回組內每一列的明細，就要再包一層查詢。

## FLOAT 與 DECIMAL

| 寫法 | 型別 | 0.1 + 0.2 的結果 | 等於 0.3？ |
|---|---|---|---|
| `0.1E0 + 0.2E0` | `FLOAT` | `0.30000000000000004` | 不相等 |
| `0.1 + 0.2` | `DECIMAL` | `0.3` | 相等 |

- `E0` 是科學記號，SQL Server 會把它當成 `FLOAT`；沒有 E 的小數是 `DECIMAL`。
- `FLOAT` 以二進位近似儲存，0.1 無法精確表示；誤差在加總或對帳時會累積。
- 金額與價格一律用 `DECIMAL`。

## 驗收：用自己的話回答

### WHERE 與 HAVING 的差別
- 對象的不同，WHERE 是對 row 設定條件，HAVING 是對 group 設定條件
- 時機的不同，WHERE 在分組前篩選，所以不能用聚合函數；HAVING 在分組後篩選，可以用聚合函數。例如 `HAVING AVG(close_price) > 100` 改成 `WHERE` 會報錯。


### 為什麼 WHERE 裡不能用 SELECT 取的別名
- 因為 SELECT 的執行順序在 WHERE 後面，執行 WHERE 時別名還不存在
- 排在 SELECT 之後的 ORDER BY 就能用別名（查詢 5 的 `ORDER BY avg_price DESC`）


### COUNT(*) 與 COUNT(欄位) 遇到 NULL 的差別
- COUNT(*) 會計算 row 的總數，無論是否有欄位為 NULL。COUNT(欄位) 則會計算某特定欄位不為 NULL 的列數。
- 本次 `COUNT(*)` 是 10、`COUNT(dividend)` 是 8，差的 2 列是股利為 NULL 的聯電、緯創。


## 踩到的坑
- 有 `GROUP BY` 時，`SELECT` 只能放分組欄位或聚合函數；加上 `stock_name` 會報錯，因為一組有多檔股票，SQL Server 不知道要顯示哪個名稱。
  錯誤訊息關鍵字：`is invalid in the select list because it is not contained in either an aggregate function or the GROUP BY clause`。
- 要列出「平均價 > 100 的產業」裡的每檔股票，要用子查詢：內層 `GROUP BY` + `HAVING` 找出產業，外層 `WHERE industry IN (…)` 取回明細。


## 驗收

- [x] 能解釋 `WHERE` 與 `HAVING` 的差別
- [x] 能解釋為什麼 `WHERE` 裡不能用 `SELECT` 取的別名
- [x] 能解釋 `COUNT(*)` 與 `COUNT(欄位)` 遇到 NULL 的差別
