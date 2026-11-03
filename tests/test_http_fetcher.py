from datetime import date

import pytest
import requests

from crawler.http_fetcher import HttpFetcher


class FakeResponse:
    def __init__(self, payload=None, not_json=False):
        self._payload = payload
        self._not_json = not_json

    def raise_for_status(self):
        pass

    def json(self):
        if self._not_json:
            raise ValueError("not json")
        return self._payload


@pytest.fixture
def fetcher(tmp_path):
    return HttpFetcher(cache_dir=tmp_path, min_interval=0)


def test_cache_round_trip(fetcher, tmp_path):
    fetcher.write_cache("daily_quotes", date(2026, 10, 29), {"stat": "OK", "名稱": "台積電"})

    assert (tmp_path / "daily_quotes" / "20261029.json").exists()
    assert fetcher.read_cache("daily_quotes", date(2026, 10, 29)) == {"stat": "OK", "名稱": "台積電"}


def test_read_cache_missing_returns_none(fetcher):
    assert fetcher.read_cache("daily_quotes", date(2026, 10, 29)) is None


def test_get_json_retries_until_json(fetcher, monkeypatch):
    responses = [requests.ConnectionError(), FakeResponse(not_json=True), FakeResponse({"stat": "OK"})]

    def fake_get(*args, **kwargs):
        result = responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(fetcher._session, "get", fake_get)
    assert fetcher.get_json("https://example.com", {}) == {"stat": "OK"}


def test_get_json_raises_after_max_retries(fetcher, monkeypatch):
    calls = []

    def fake_get(*args, **kwargs):
        calls.append(1)
        raise requests.ConnectionError()

    monkeypatch.setattr(fetcher._session, "get", fake_get)
    with pytest.raises(requests.ConnectionError):
        fetcher.get_json("https://example.com", {})
    assert len(calls) == 3
