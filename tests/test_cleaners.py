from datetime import date
from decimal import Decimal

from crawler.cleaners import parse_number, parse_roc_date


def test_parse_number_thousand_separator():
    assert parse_number("1,234.5") == Decimal("1234.5")


def test_parse_number_missing_returns_none():
    assert parse_number("-") is None
    assert parse_number("--") is None
    assert parse_number("") is None


def test_parse_roc_date():
    assert parse_roc_date("115/10/20") == date(2026, 10, 20)
