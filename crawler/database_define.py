"""對應資料庫表名、欄位名與 CHECK 約束值，寫入／查詢時一律從此處取用。"""


class Table:
    STOCKS = "dbo.stocks"
    DAILY_PRICES = "dbo.daily_prices"
    DAILY_VALUATIONS = "dbo.daily_valuations"
    CRAWL_STATUS = "dbo.crawl_status"
    BACKFILL_REQUESTS = "dbo.backfill_requests"
    ETL_LOG = "dbo.etl_log"


class Col:
    STOCK_ID = "stock_id"
    STOCK_NAME = "stock_name"
    INDUSTRY = "industry"
    MARKET = "market"
    SECURITY_TYPE = "security_type"
    LISTING_STATUS = "listing_status"

    TRADE_DATE = "trade_date"
    OPEN_PRICE = "open_price"
    HIGH_PRICE = "high_price"
    LOW_PRICE = "low_price"
    CLOSE_PRICE = "close_price"
    TRADE_VOLUME = "trade_volume"
    TRADE_VALUE = "trade_value"

    PRICE_TO_EARNINGS_RATIO = "price_to_earnings_ratio"
    DIVIDEND_YIELD = "dividend_yield"
    PRICE_TO_BOOK_RATIO = "price_to_book_ratio"

    DATASET = "dataset"
    STATUS = "status"

    ID = "id"
    START_DATE = "start_date"
    END_DATE = "end_date"
    IS_FORCE_BACKFILL = "is_force_backfill"
    CREATED_TIME = "created_time"
    FINISHED_TIME = "finished_time"

    LOAD_COUNT = "load_count"
    ERROR_MESSAGE = "error_message"


class Stocks:
    TABLE = Table.STOCKS
    UPSERT_COLUMNS = [
        Col.STOCK_ID,
        Col.STOCK_NAME,
        Col.MARKET,
        Col.SECURITY_TYPE,
    ]


class DailyPrices:
    TABLE = Table.DAILY_PRICES
    UPSERT_COLUMNS = [
        Col.STOCK_ID,
        Col.TRADE_DATE,
        Col.OPEN_PRICE,
        Col.HIGH_PRICE,
        Col.LOW_PRICE,
        Col.CLOSE_PRICE,
        Col.TRADE_VOLUME,
        Col.TRADE_VALUE,
    ]


class DailyValuations:
    TABLE = Table.DAILY_VALUATIONS
    UPSERT_COLUMNS = [
        Col.STOCK_ID,
        Col.TRADE_DATE,
        Col.PRICE_TO_EARNINGS_RATIO,
        Col.DIVIDEND_YIELD,
        Col.PRICE_TO_BOOK_RATIO,
    ]


class CrawlStatusTable:
    TABLE = Table.CRAWL_STATUS


class EtlLog:
    TABLE = Table.ETL_LOG


class SecurityType:
    STOCK = "STOCK"
    ETF = "ETF"
    BOND_ETF = "BOND_ETF"


class ListingStatus:
    LISTED = "LISTED"
    DELISTED = "DELISTED"


class Market:
    TWSE = "TWSE"
    TPEX = "TPEX"
    EMERGING = "EMERGING"


class CrawlStatus:
    SUCCESS = "SUCCESS"
    NO_DATA = "NO_DATA"
    FAILED = "FAILED"


class BackfillStatus:
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EtlStatus:
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
