from datetime import date
from decimal import Decimal

from crawler.cleaners import parse_number
from crawler.crawler_config import CrawlerConfig
from crawler.database_define import Col
from crawler.http_fetcher import HttpFetcher


class TwseClient:
    def __init__(self, fetcher: HttpFetcher | None = None, config: CrawlerConfig | None = None):
        self._fetcher = fetcher or HttpFetcher()
        self._config = config or CrawlerConfig()

    def fetch_raw(self, key: str, trade_date: date) -> dict | None:
        """取得指定資料集某日的原始 JSON；非交易日回傳 None。"""
        cached = self._fetcher.read_cache(key, trade_date)
        if cached is not None:
            return cached

        params = {**self._config.params(key), "date": f"{trade_date:%Y%m%d}"}
        payload = self._fetcher.get_json(self._config.url(key), params)
        if payload.get("stat") != "OK":
            return None
        if payload.get("date") != f"{trade_date:%Y%m%d}":
            raise ValueError(f"{key} 回傳的日期 {payload.get('date')} 與要求的 {trade_date} 不符")

        # 只快取 stat 為 OK 的回應，休市回應與錯誤頁不留快取
        self._fetcher.write_cache(key, trade_date, payload)
        return payload

    def fetch_daily_quotes(self, trade_date: date) -> list[dict]:
        """找到給定日期的股票交易行情；非交易日回傳空清單。"""
        payload = self.fetch_raw("daily_quotes", trade_date)
        if payload is None:
            return []

        # 回應有多張表（大盤指數、統計等），以欄位找出個股行情那張，不依賴表的順序
        table = next(t for t in payload["tables"] if "證券代號" in t.get("fields", []))
        col = {name: i for i, name in enumerate(table["fields"])}
        return [
            {
                Col.STOCK_ID: row[col["證券代號"]].strip(),
                Col.STOCK_NAME: row[col["證券名稱"]].strip(),
                Col.TRADE_DATE: trade_date,
                Col.OPEN_PRICE: parse_number(row[col["開盤價"]]),
                Col.HIGH_PRICE: parse_number(row[col["最高價"]]),
                Col.LOW_PRICE: parse_number(row[col["最低價"]]),
                Col.CLOSE_PRICE: parse_number(row[col["收盤價"]]),
                Col.TRADE_VOLUME: _to_int(parse_number(row[col["成交股數"]])),
                Col.TRADE_VALUE: _to_int(parse_number(row[col["成交金額"]])),
            }
            for row in table["data"]
        ]

    def fetch_daily_valuations(self, trade_date: date) -> list[dict]:
        """找到給定日期的本益比、殖利率、股價淨值比等資料；非交易日回傳空清單。"""
        payload = self.fetch_raw("daily_valuations", trade_date)
        if payload is None:
            return []

        col = {name: i for i, name in enumerate(payload["fields"])}
        return [
            {
                Col.STOCK_ID: row[col["證券代號"]].strip(),
                Col.TRADE_DATE: trade_date,
                Col.PRICE_TO_EARNINGS_RATIO: parse_number(row[col["本益比"]]),
                Col.DIVIDEND_YIELD: parse_number(row[col["殖利率(%)"]]),
                Col.PRICE_TO_BOOK_RATIO: parse_number(row[col["股價淨值比"]]),
            }
            for row in payload["data"]
        ]


def _to_int(value: Decimal | None) -> int | None:
    return None if value is None else int(value)
