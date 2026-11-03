import pytest

from crawler.crawler_config import CrawlerConfig


@pytest.fixture
def config(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text(
        '[datasets.daily_quotes]\n'
        'url = "https://example.com/MI_INDEX"\n'
        'params = { type = "ALLBUT0999", response = "json" }\n',
        encoding="utf-8",
    )
    return CrawlerConfig(path)


def test_url_and_params_by_key(config):
    assert config.url("daily_quotes") == "https://example.com/MI_INDEX"
    assert config.params("daily_quotes") == {"type": "ALLBUT0999", "response": "json"}


def test_params_returns_copy(config):
    config.params("daily_quotes")["date"] = "20261029"
    assert "date" not in config.params("daily_quotes")


def test_unknown_key_raises(config):
    with pytest.raises(KeyError):
        config.url("missing")


def test_default_config_has_crawler_datasets():
    config = CrawlerConfig()
    assert config.url("daily_quotes").endswith("/MI_INDEX")
    assert config.url("daily_valuations").endswith("/BWIBBU_d")
