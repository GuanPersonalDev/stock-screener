# Day 1｜環境建置、第一個查詢

日期：2026-10-20　對應 Issue：#1

## 做了什麼

1. 寫 `docker-compose.yml`、`.env`、`.env.example`、`.gitattributes`
2. `docker compose up -d` 啟動 SQL Server 2022（Apple Silicon 透過 Rosetta 模擬 x86_64）
3. 用 Cursor 的 MSSQL 擴充套件以 `sa` 連線
4. 跑第一批查詢，建立 `StockLab` 資料庫

```sql
SELECT @@SERVERNAME, @@VERSION;
SELECT GETDATE();
CREATE DATABASE StockLab;
SELECT name FROM sys.databases;
```

## 檔案各自的用途

| 檔案 | 用途 | 進 git |
|---|---|---|
| `docker-compose.yml` | 定義 SQL Server 容器：映像、平台、環境變數、連接埠、volume | 是 |
| `.env` | 存 SA 密碼，compose 啟動時自動讀取 | 否（`.gitignore` 排除） |
| `.env.example` | 告訴其他機器 `.env` 要有哪些鍵 | 是 |
| `.gitattributes` | `* text=auto eol=lf`，避免 Windows 把檔案轉成 CRLF | 是 |

## docker-compose.yml 的重點

- `platform: linux/amd64`：SQL Server 映像只有 x86_64 版，Mac 靠 Rosetta 模擬，Windows 原生執行，兩台機器共用同一份設定。
- `ACCEPT_EULA: "Y"`：同意 Microsoft 的授權條款，沒有設定容器會直接結束。未指定 `MSSQL_PID` 時預設是 Developer 版，功能完整但只能用於開發測試。
- `MSSQL_SA_PASSWORD: ${MSSQL_SA_PASSWORD}`：從 `.env` 代入，密碼不出現在 compose 檔裡。
- `volumes: - mssql-data:/var/opt/mssql`：把資料庫檔案存在 Docker 管理的具名 volume，容器刪掉重建資料仍在。
- 最外層的 `volumes:` 是宣告具名 volume，不是容器名稱。

同一份檔案裡有三種名字：

| 名字 | 例子 | 用在哪 |
|---|---|---|
| service 名稱 | `mssql` | `docker compose logs mssql` |
| 容器名稱 | `stocklab-mssql` | `docker ps` 顯示的名稱 |
| volume 名稱 | `mssql-data` | 實際名稱會加上專案資料夾前綴：`sql-stock-screener_mssql-data` |

## SQL Server 的基本認識

- `sa`（system administrator）是 SQL Server 內建的最高權限帳號，Docker 映像只開放設定它的密碼。
  正式環境通常停用 `sa`，另建權限最小的帳號給應用程式使用（最小權限原則）。
- SA 密碼只在第一次建立資料時寫入；之後改 `.env` 不會改到密碼，要用 `ALTER LOGIN sa WITH PASSWORD = ...`。
- `@@` 開頭的是系統變數，`GETDATE()` 是函式，兩者都不需要 `FROM`。
- `SELECT` 只讀取資料，不會修改任何東西。

系統資料庫：

| 資料庫 | 用途 |
|---|---|
| `master` | 伺服器設定、登入帳號、所有資料庫的清單 |
| `tempdb` | 暫存表與排序的中間結果，每次重啟清空 |
| `model` | 新建資料庫的範本 |
| `msdb` | SQL Agent 排程作業、備份紀錄 |



## 用自己的話說明：database、schema、table 的差別
- database 是一份資料庫，在一個 SQL Server 中可以存在很多 database
- schema 是 database 內的命名空間, 類似資料夾的概念, 用來把 table, view, 預存程序做分組
- table 則放在 schema 中, 是一份表格資料


## 踩到的坑

- 密碼至少 8 碼，且包含大寫、小寫、數字、符號其中三種，否則容器啟動失敗；密碼避開 `$`，compose 會把它當成變數。
- 本機是自簽憑證，Cursor 連線要勾選 Trust server certificate。
- 新版 MSSQL 擴充套件的側邊欄顯示的是 Profile name，不是 `localhost`。
- logs 裡的 `Failed to open password policy registry path` 不是錯誤，Linux 版沒有 Windows 登錄檔，改用預設密碼政策。
- 不要執行 `docker compose down -v`，`-v` 會連 volume 一起刪掉。


## 驗收

- [x] 重開容器後 `StockLab` 還在（`docker compose down` → `docker compose up -d` → 查 `sys.databases`）
- [x] 密碼只在 `.env`，沒有進 git（`git check-ignore .env`）
- [x] 能說出 database、schema、table 的差別
