# 環境建置

本機：macOS（Apple Silicon）、Docker Desktop、Python 3.13。

## 1. SQL Server（Docker）

SQL Server 官方映像只有 x86_64 版本，Apple Silicon 要靠 Rosetta 模擬執行。

1. 打開 Docker Desktop → Settings → General，勾選
   **Use Rosetta for x86_64/amd64 emulation on Apple Silicon**，套用後重啟
2. 在專案根目錄建立 `.env`（已在 `.gitignore`，不會進版控）：

   ```
   MSSQL_SA_PASSWORD=<自己設定>
   ```

   密碼至少 8 碼，且包含大寫、小寫、數字、符號其中三種，否則容器會啟動失敗。

3. 自己寫一份 `docker-compose.yml`，重點如下（當作第一個練習，寫完再看下面的提示）：
   - 映像：`mcr.microsoft.com/mssql/server:2022-latest`
   - `platform: linux/amd64`
   - 環境變數：`ACCEPT_EULA=Y`、`MSSQL_SA_PASSWORD`（從 `.env` 帶入）
   - 連接埠：`1433:1433`
   - volume：掛到容器內的 `/var/opt/mssql`，否則刪掉容器資料就沒了

4. `docker compose up -d`，再用 `docker compose logs -f` 看到
   `SQL Server is now ready for client connections` 就是啟動完成

> 舊教學常提到 Azure SQL Edge（原生支援 ARM），它已於 2025 年 9 月停止支援，不要用。

## 2. 查詢工具

- **VS Code + MSSQL 擴充套件**（推薦）：連線 `localhost`、帳號 `sa`、勾選 Trust server certificate
- 命令列：`brew install sqlcmd`，用 `sqlcmd -S localhost -U sa -C` 連線

> Azure Data Studio 已退役，舊教學若提到它，改用 VS Code MSSQL 擴充套件。

## 3. Python 套件

建議用 `uv` 管理：

```bash
uv init --python 3.13
```

需要的套件：

| 套件 | 用途 |
|---|---|
| `requests` | 爬蟲 |
| `pandas` | 資料清理 |
| `pymssql` | 連 SQL Server（免裝 ODBC 驅動，最簡單） |
| `sqlalchemy` | 選用：和 pandas 搭配寫入 |
| `python-dotenv` | 讀 `.env` |
| `streamlit` | 面板 |

業界更常見的是 `pyodbc`，但它要另外安裝 Microsoft ODBC Driver 18。
先用 `pymssql` 跑通，有餘力再換成 `pyodbc` 當加分項。

## 4. 資料來源：台灣證券交易所

| 資料 | 端點（Day 6 先用瀏覽器確認，改版以官網為準） |
|---|---|
| 每日全部個股收盤行情 | `https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date=YYYYMMDD&type=ALLBUT0999&response=json` |
| 每日本益比、殖利率、股價淨值比 | `https://www.twse.com.tw/rwd/zh/afterTrading/BWIBBU_d?date=YYYYMMDD&selectType=ALL&response=json` |
| 單一個股整月行情 | `https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?date=YYYYMMDD&stockNo=2330&response=json` |
| OpenAPI（只有最新一日） | `https://openapi.twse.com.tw/` |

證交所對短時間大量請求會暫時封鎖 IP，每次請求間隔 3 秒以上。
