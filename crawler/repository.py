from contextlib import contextmanager
import os
from datetime import date
from typing import Self

import pymssql
from dotenv import load_dotenv

from crawler.database_define import (
    Col,
    CrawlStatusTable,
    DailyPrices,
    DailyValuations,
    EtlLog,
    Stocks,
)

CREATE_STAGING_SQL = """
DROP TABLE IF EXISTS #staging;
SELECT TOP 0 {columns} INTO #staging FROM {table};
"""

MERGE_STOCK_SQL = """
MERGE dbo.stocks AS t
USING #staging AS s
    ON t.stock_id = s.stock_id
WHEN MATCHED AND EXISTS(
        SELECT s.stock_name, s.security_type
        EXCEPT
        SELECT t.stock_name, t.security_type)
    THEN UPDATE SET stock_name = s.stock_name,
        security_type = s.security_type
WHEN NOT MATCHED BY TARGET 
    THEN INSERT (stock_id, stock_name, market, security_type)
    VALUES (s.stock_id, s.stock_name, s.market, s.security_type);
"""

MERGE_DAILY_PRICE_SQL = """
MERGE dbo.daily_prices AS t
USING #staging AS s
    ON t.stock_id = s.stock_id AND t.trade_date = s.trade_date
WHEN MATCHED AND EXISTS (
    SELECT s.open_price, s.high_price, s.low_price, s.close_price, s.trade_volume, s.trade_value
    EXCEPT 
    SELECT t.open_price, t.high_price, t.low_price, t.close_price, t.trade_volume, t.trade_value)
THEN UPDATE SET open_price = s.open_price, high_price = s.high_price, low_price = s.low_price, close_price = s.close_price, trade_volume = s.trade_volume, trade_value = s.trade_value
WHEN NOT MATCHED BY TARGET
    THEN INSERT (stock_id, trade_date, open_price, high_price, low_price, close_price, trade_volume, trade_value)
    VALUES (s.stock_id, s.trade_date, s.open_price, s.high_price, s.low_price, s.close_price, s.trade_volume, s.trade_value);
"""

MERGE_VALUATIONS_SQL = """
MERGE dbo.daily_valuations AS t
USING #staging AS s
   ON t.stock_id = s.stock_id AND t.trade_date = s.trade_date
WHEN MATCHED AND EXISTS (
        SELECT s.price_to_earnings_ratio, s.dividend_yield, s.price_to_book_ratio
        EXCEPT
        SELECT t.price_to_earnings_ratio, t.dividend_yield, t.price_to_book_ratio)
    THEN UPDATE SET price_to_earnings_ratio = s.price_to_earnings_ratio,
                    dividend_yield = s.dividend_yield,
                    price_to_book_ratio = s.price_to_book_ratio
WHEN NOT MATCHED BY TARGET
    THEN INSERT (stock_id, trade_date, price_to_earnings_ratio, dividend_yield, price_to_book_ratio)
         VALUES (s.stock_id, s.trade_date, s.price_to_earnings_ratio, s.dividend_yield, s.price_to_book_ratio);
"""

MERGE_CRAW_STATUS_SQL = """
MERGE dbo.crawl_status AS t
USING (VALUES (%s, %s, %s)) AS s(dataset, trade_date, status)
    ON t.dataset = s.dataset AND t.trade_date = s.trade_date
WHEN MATCHED AND t.status <> s.status
    THEN UPDATE SET status = s.status
WHEN NOT MATCHED BY TARGET
    THEN INSERT (dataset, trade_date, status) VALUES (s.dataset, s.trade_date, s.status);
"""

class StockRepository:
    """
    爬蟲寫入資料庫的入口, 負責將清理好的資料寫進 SQL Server, 也記錄批次狀態
    """
    def __init__(self, conn: pymssql.Connection):
        self._conn = conn

    @classmethod
    def from_env(cls) -> Self:
        load_dotenv()
        conn = pymssql.connect(
            server=os.environ["MSSQL_HOST"],
            port=os.environ["MSSQL_PORT"],
            user="sa",
            password=os.environ["MSSQL_SA_PASSWORD"],
            database=os.environ["MSSQL_DATABASE"],
            autocommit=False,
        )
        return cls(conn)

    def close(self) -> None:
        self._conn.close()

    @contextmanager
    def transaction(self):
        try:
            yield
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def _merge_via_staging(self, table: str, columns: list[str], rows: list[dict], merge_sql: str) -> int:
        if not rows:
            return 0
        cols = ", ".join(columns)
        placeholder = ", ".join(["%s"] * len(columns))
        with self._conn.cursor() as cur:
            cur.execute(CREATE_STAGING_SQL.format(table=table, columns=cols))
            cur.executemany(f"INSERT INTO #staging ({cols}) VALUES ({placeholder})", [tuple(r[c] for c in columns) for r in rows])
            cur.execute(merge_sql)
            return cur.rowcount

    def upsert_stocks(self, rows: list[dict]) -> int:
        return self._merge_via_staging(
            Stocks.TABLE, Stocks.UPSERT_COLUMNS, rows, MERGE_STOCK_SQL
        )

    def upsert_daily_prices(self, rows: list[dict]) -> int:
        return self._merge_via_staging(
            DailyPrices.TABLE, DailyPrices.UPSERT_COLUMNS, rows, MERGE_DAILY_PRICE_SQL
        )

    def upsert_valuations(self, rows: list[dict]) -> int:
        return self._merge_via_staging(
            DailyValuations.TABLE, DailyValuations.UPSERT_COLUMNS, rows, MERGE_VALUATIONS_SQL
        )

    def mark_crawl_status(self, dataset: str, trade_date: date, status: str) -> None:
        with self._conn.cursor() as cur:
            cur.execute(MERGE_CRAW_STATUS_SQL, (dataset, trade_date, status))

    def get_crawl_status(self, dataset: str, start: date, end: date) -> dict[date, str]:
        with self._conn.cursor() as cur:
            cur.execute(
                f"SELECT {Col.TRADE_DATE}, {Col.STATUS} FROM {CrawlStatusTable.TABLE} "
                f"WHERE {Col.DATASET} = %s AND {Col.TRADE_DATE} BETWEEN %s AND %s",
                (dataset, start, end),
            )
            return {d: s for d, s in cur.fetchall()}

    def write_etl_log(self, trade_date: date, status: str, rows: int, error: str | None = None) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {EtlLog.TABLE} "
                f"({Col.TRADE_DATE}, {Col.STATUS}, {Col.LOAD_COUNT}, {Col.ERROR_MESSAGE}) "
                f"VALUES (%s, %s, %s, %s)",
                (trade_date, status, rows, error),
            )
