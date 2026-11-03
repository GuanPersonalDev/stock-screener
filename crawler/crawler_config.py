import tomllib
from pathlib import Path

DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.toml"


class CrawlerConfig:
    def __init__(self, path: Path = DEFAULT_CONFIG_PATH):
        with path.open("rb") as f:
            self._datasets = tomllib.load(f)["datasets"]

    def url(self, key: str) -> str:
        """回傳該資料集的 url；key 不存在時丟出 KeyError。"""
        return self._datasets[key]["url"]

    def params(self, key: str) -> dict:
        """回傳該資料集的固定查詢參數（不含日期）；key 不存在時丟出 KeyError。"""
        return dict(self._datasets[key].get("params", {}))
