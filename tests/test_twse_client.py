from datetime import date
from decimal import Decimal

import pytest

from crawler.http_fetcher import HttpFetcher
from crawler.twse_client import TwseClient

TRADE_DATE = date(2026, 10, 29)

QUOTES_PAYLOAD = {
    "stat": "OK",
    "date": "20261029",
    "tables": [
        {"title": "價格指數", "fields": ["指數", "收盤指數"], "data": [["發行量加權股價指數", "23,000.00"]]},
        {
            "title": "每日收盤行情",
            "fields": ["證券代號", "證券名稱", "成交股數", "成交筆數", "成交金額",
                       "開盤價", "最高價", "最低價", "收盤價", "漲跌(+/-)"],
            "data": [
                ["2330", "台積電", "29,745,814", "10,539", "428,344,232",
                 "1,450.00", "1,465.00", "1,440.00", "1,460.00", "<p style= color:red>+</p>"],
                ["00625K", "富邦上証+R", "0", "0", "0", "--", "--", "--", "--", "<p> </p>"],
            ],
        },
    ],
}

VALUATIONS_PAYLOAD = {
    "stat": "OK",
    "date": "20261029",
    "fields": ["證券代號", "證券名稱", "收盤價", "殖利率(%)", "股利年度", "本益比", "股價淨值比", "財報年/季"],
    "data": [["1101", "台泥", "28.20", "2.84", 114, "-", "0.91", "115/2"]],
}


@pytest.fixture
def fetcher(tmp_path):
    return HttpFetcher(cache_dir=tmp_path, min_interval=0)


def stub_get_json(monkeypatch, fetcher, payload):
    calls = []

    def fake_get_json(url, params):
        calls.append((url, params))
        return payload

    monkeypatch.setattr(fetcher, "get_json", fake_get_json)
    return calls


def test_fetch_daily_quotes_parses_stock_table(fetcher, monkeypatch):
    stub_get_json(monkeypatch, fetcher, QUOTES_PAYLOAD)

    rows = TwseClient(fetcher=fetcher).fetch_daily_quotes(TRADE_DATE)

    assert rows[0] == {
        "stock_id": "2330",
        "stock_name": "台積電",
        "trade_date": TRADE_DATE,
        "open_price": Decimal("1450.00"),
        "high_price": Decimal("1465.00"),
        "low_price": Decimal("1440.00"),
        "close_price": Decimal("1460.00"),
        "trade_volume": 29745814,
        "trade_value": 428344232,
    }
    assert rows[1]["close_price"] is None


def test_fetch_daily_valuations_dash_becomes_none(fetcher, monkeypatch):
    stub_get_json(monkeypatch, fetcher, VALUATIONS_PAYLOAD)

    rows = TwseClient(fetcher=fetcher).fetch_daily_valuations(TRADE_DATE)

    assert rows == [{
        "stock_id": "1101",
        "trade_date": TRADE_DATE,
        "price_to_earnings_ratio": None,
        "dividend_yield": Decimal("2.84"),
        "price_to_book_ratio": Decimal("0.91"),
    }]


def test_request_params_include_date(fetcher, monkeypatch):
    calls = stub_get_json(monkeypatch, fetcher, VALUATIONS_PAYLOAD)

    TwseClient(fetcher=fetcher).fetch_daily_valuations(TRADE_DATE)

    url, params = calls[0]
    assert url.endswith("/BWIBBU_d")
    assert params == {"selectType": "ALL", "response": "json", "date": "20261029"}


def test_second_fetch_uses_cache(fetcher, monkeypatch):
    calls = stub_get_json(monkeypatch, fetcher, QUOTES_PAYLOAD)
    client = TwseClient(fetcher=fetcher)

    client.fetch_daily_quotes(TRADE_DATE)
    client.fetch_daily_quotes(TRADE_DATE)

    assert len(calls) == 1


def test_non_trading_day_returns_empty_and_not_cached(fetcher, monkeypatch):
    calls = stub_get_json(monkeypatch, fetcher, {"stat": "很抱歉，沒有符合條件的資料!"})
    client = TwseClient(fetcher=fetcher)

    assert client.fetch_daily_quotes(date(2026, 10, 25)) == []
    assert client.fetch_daily_valuations(date(2026, 10, 25)) == []
    assert fetcher.read_cache("daily_quotes", date(2026, 10, 25)) is None
    assert len(calls) == 2


def test_mismatched_date_raises(fetcher, monkeypatch):
    stub_get_json(monkeypatch, fetcher, {**VALUATIONS_PAYLOAD, "date": "20261028"})

    with pytest.raises(ValueError):
        TwseClient(fetcher=fetcher).fetch_daily_valuations(TRADE_DATE)
