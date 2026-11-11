from datetime import date
from decimal import Decimal

from crawler.database_define import SecurityType


def parse_number(raw: str) -> Decimal | None:
    if raw in ("-", "--", ""):
        return None
    return Decimal(raw.replace(",", ""))


def parse_roc_date(raw: str) -> date:
    year_str, month_str, day_str = raw.split("/")
    return date(int(year_str) + 1911, int(month_str), int(day_str))


def classify_security_type(stock_id: str) -> str:
    """
    00 開頭為 ETF, 以 B 為結尾為債券 ETF
    其餘為股票
    """
    if stock_id.startswith("00"):
        return SecurityType.BOND_ETF if stock_id.endswith("B") else SecurityType.ETF
    return SecurityType.STOCK
