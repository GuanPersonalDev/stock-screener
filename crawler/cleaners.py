from datetime import date
from decimal import Decimal


def parse_number(raw: str) -> Decimal | None:
    if raw in ("-", "--", ""):
        return None
    return Decimal(raw.replace(",", ""))


def parse_roc_date(raw: str) -> date:
    year_str, month_str, day_str = raw.split("/")
    return date(int(year_str) + 1911, int(month_str), int(day_str))
