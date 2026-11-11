"""StockRepository 整合測試：連 Docker 裡的真實 SQL Server，連不上就 skip。

測試資料只用 ZZTEST 開頭的代號、遠古交易日與專屬 dataset，setup／teardown 都會清掉。
"""
from datetime import date
from decimal import Decimal

import pymssql
import pytest

from crawler.repository import StockRepository

TEST_DATE = date(1999, 1, 4)
TEST_DATASET = "test_dataset"
TEST_STOCK_IDS = ("ZZTEST1", "ZZTEST2")


def _purge(conn) -> None:
    placeholders = ", ".join(["%s"] * len(TEST_STOCK_IDS))
    with conn.cursor() as cur:
        cur.execute(f"DELETE FROM dbo.daily_prices WHERE stock_id IN ({placeholders})", TEST_STOCK_IDS)
        cur.execute(f"DELETE FROM dbo.daily_valuations WHERE stock_id IN ({placeholders})", TEST_STOCK_IDS)
        cur.execute("DELETE FROM dbo.crawl_status WHERE dataset = %s", (TEST_DATASET,))
        cur.execute("DELETE FROM dbo.etl_log WHERE trade_date = %s", (TEST_DATE,))
        cur.execute(f"DELETE FROM dbo.stocks WHERE stock_id IN ({placeholders})", TEST_STOCK_IDS)
    conn.commit()


@pytest.fixture
def repo():
    try:
        repository = StockRepository.from_env()
    except (pymssql.Error, KeyError) as exc:
        pytest.skip(f"無法連線資料庫：{type(exc).__name__}")
    _purge(repository._conn)
    yield repository
    try:
        repository._conn.rollback()
        _purge(repository._conn)
    finally:
        repository.close()


@pytest.fixture
def query(repo):
    def run(sql: str, params: tuple = ()):
        with repo._conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    return run


@pytest.fixture
def stock_rows() -> list[dict]:
    return [
        {"stock_id": "ZZTEST1", "stock_name": "測試一", "market": "TWSE", "security_type": "STOCK"},
        {"stock_id": "ZZTEST2", "stock_name": "測試二", "market": "TWSE", "security_type": "ETF"},
    ]


@pytest.fixture
def price_rows() -> list[dict]:
    return [
        {
            "stock_id": "ZZTEST1", "trade_date": TEST_DATE,
            "open_price": Decimal("10.00"), "high_price": Decimal("12.00"),
            "low_price": Decimal("9.50"), "close_price": Decimal("11.00"),
            "trade_volume": 1000, "trade_value": 11000,
        },
        {
            "stock_id": "ZZTEST2", "trade_date": TEST_DATE,
            "open_price": Decimal("20.00"), "high_price": Decimal("21.00"),
            "low_price": Decimal("19.00"), "close_price": Decimal("20.50"),
            "trade_volume": 2000, "trade_value": 41000,
        },
    ]


@pytest.fixture
def valuation_rows() -> list[dict]:
    return [
        {"stock_id": "ZZTEST1", "trade_date": TEST_DATE,
         "price_to_earnings_ratio": Decimal("15.50"), "dividend_yield": Decimal("2.84"),
         "price_to_book_ratio": Decimal("0.91")},
        {"stock_id": "ZZTEST2", "trade_date": TEST_DATE,
         "price_to_earnings_ratio": None, "dividend_yield": Decimal("1.00"),
         "price_to_book_ratio": Decimal("1.20")},
    ]


@pytest.fixture
def seeded_stocks(repo, stock_rows):
    with repo.transaction():
        repo.upsert_stocks(stock_rows)


class TestStockRepository:
    def test_upsert_twice_keeps_count_and_second_returns_zero(self, repo, query, stock_rows, price_rows):
        with repo.transaction():
            repo.upsert_stocks(stock_rows)
            first = repo.upsert_daily_prices(price_rows)
        with repo.transaction():
            repo.upsert_stocks(stock_rows)
            second = repo.upsert_daily_prices(price_rows)

        count = query("SELECT COUNT(*) FROM dbo.daily_prices WHERE trade_date = %s", (TEST_DATE,))[0][0]
        stock_count = query("SELECT COUNT(*) FROM dbo.stocks WHERE stock_id LIKE 'ZZTEST%'")[0][0]
        assert first == len(price_rows)
        assert second == 0
        assert count == len(price_rows)
        assert stock_count == len(stock_rows)

    def test_changed_close_price_returns_one_and_updates(self, repo, query, seeded_stocks, price_rows):
        with repo.transaction():
            repo.upsert_daily_prices(price_rows)
        price_rows[0]["close_price"] = Decimal("11.50")

        with repo.transaction():
            affected = repo.upsert_daily_prices(price_rows)

        close = query(
            "SELECT close_price FROM dbo.daily_prices WHERE stock_id = %s AND trade_date = %s",
            ("ZZTEST1", TEST_DATE),
        )[0][0]
        assert affected == 1
        assert close == Decimal("11.50")

    def test_null_old_value_is_updated_to_number(self, repo, query, seeded_stocks, price_rows):
        price_rows[0]["close_price"] = None
        with repo.transaction():
            repo.upsert_daily_prices(price_rows)
        price_rows[0]["close_price"] = Decimal("11.00")

        with repo.transaction():
            affected = repo.upsert_daily_prices(price_rows)

        close = query(
            "SELECT close_price FROM dbo.daily_prices WHERE stock_id = %s AND trade_date = %s",
            ("ZZTEST1", TEST_DATE),
        )[0][0]
        assert affected == 1
        assert close == Decimal("11.00")

    def test_exception_in_transaction_rolls_back_all_writes(self, repo, query, stock_rows, price_rows):
        with pytest.raises(RuntimeError):
            with repo.transaction():
                repo.upsert_stocks(stock_rows)
                repo.upsert_daily_prices(price_rows)
                raise RuntimeError("boom")

        prices = query("SELECT COUNT(*) FROM dbo.daily_prices WHERE trade_date = %s", (TEST_DATE,))[0][0]
        stocks = query("SELECT COUNT(*) FROM dbo.stocks WHERE stock_id LIKE 'ZZTEST%'")[0][0]
        assert prices == 0
        assert stocks == 0

    def test_upsert_valuations_writes_rows_including_null_pe(self, repo, query, seeded_stocks, valuation_rows):
        with repo.transaction():
            affected = repo.upsert_valuations(valuation_rows)

        rows = query(
            "SELECT stock_id, price_to_earnings_ratio, dividend_yield, price_to_book_ratio "
            "FROM dbo.daily_valuations WHERE trade_date = %s ORDER BY stock_id",
            (TEST_DATE,),
        )
        assert affected == len(valuation_rows)
        assert rows == [
            ("ZZTEST1", Decimal("15.50"), Decimal("2.84"), Decimal("0.91")),
            ("ZZTEST2", None, Decimal("1.00"), Decimal("1.20")),
        ]

    def test_mark_crawl_status_then_update_returns_latest_with_date_keys(self, repo):
        with repo.transaction():
            repo.mark_crawl_status(TEST_DATASET, TEST_DATE, "SUCCESS")
        first = repo.get_crawl_status(TEST_DATASET, TEST_DATE, TEST_DATE)
        with repo.transaction():
            repo.mark_crawl_status(TEST_DATASET, TEST_DATE, "FAILED")
        second = repo.get_crawl_status(TEST_DATASET, TEST_DATE, TEST_DATE)

        assert first == {TEST_DATE: "SUCCESS"}
        assert second == {TEST_DATE: "FAILED"}
        assert all(type(key) is date for key in second)

    def test_write_etl_log_with_none_error_inserts_row(self, repo, query):
        with repo.transaction():
            repo.write_etl_log(TEST_DATE, "SUCCESS", 5, None)

        rows = query(
            "SELECT status, load_count, error_message FROM dbo.etl_log WHERE trade_date = %s",
            (TEST_DATE,),
        )
        assert rows == [("SUCCESS", 5, None)]

    def test_write_etl_log_with_error_message_stores_it(self, repo, query):
        with repo.transaction():
            repo.write_etl_log(TEST_DATE, "FAILED", 0, "連線逾時")

        rows = query("SELECT error_message FROM dbo.etl_log WHERE trade_date = %s", (TEST_DATE,))
        assert rows == [("連線逾時",)]

    def test_empty_rows_upsert_returns_zero(self, repo):
        assert repo.upsert_stocks([]) == 0
        assert repo.upsert_daily_prices([]) == 0
        assert repo.upsert_valuations([]) == 0
