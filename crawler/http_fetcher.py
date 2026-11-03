import json
import time
from datetime import date
from pathlib import Path

import requests


class HttpFetcher:
    def __init__(self, cache_dir: Path = Path("data/raw"), min_interval: float = 3.0, max_retries: int = 3):
        self._cache_dir = cache_dir
        self._min_interval = min_interval
        self._max_retries = max_retries
        self._session = requests.Session()
        self._last_request_at: float | None = None

    def get_json(self, url: str, params: dict) -> dict:
        """發出 GET 請求並回傳 JSON；含限速與重試，全部失敗時丟出例外。"""
        for attempt in range(1, self._max_retries + 1):
            self._throttle()
            try:
                response = self._session.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except (requests.RequestException, ValueError):
                # ValueError：回應不是 JSON，例如證交所的 HTML 封鎖頁
                if attempt == self._max_retries:
                    raise
                time.sleep(self._min_interval * 2 ** (attempt - 1))

    def read_cache(self, dataset: str, trade_date: date) -> dict | None:
        """回傳快取內容；沒有快取時回傳 None。"""
        path = self._cache_path(dataset, trade_date)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def write_cache(self, dataset: str, trade_date: date, payload: dict) -> None:
        path = self._cache_path(dataset, trade_date)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def _cache_path(self, dataset: str, trade_date: date) -> Path:
        return self._cache_dir / dataset / f"{trade_date:%Y%m%d}.json"

    def _throttle(self) -> None:
        # 讀快取不經過這裡，只有真正發出的請求才受限速
        if self._last_request_at is not None:
            wait = self._min_interval - (time.monotonic() - self._last_request_at)
            if wait > 0:
                time.sleep(wait)
        self._last_request_at = time.monotonic()
