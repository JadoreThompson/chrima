from enum import Enum


class Currency(str, Enum):
    USD = "usd"


class PriceType(str, Enum):
    ONE_TIME = "one_time"
    RECURRING = "recurring"


class RecurringInterval(str, Enum):
    DAY = "day"
    MONTH = "month"
