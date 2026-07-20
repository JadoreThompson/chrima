from enum import Enum


class TimePeriod(str, Enum):
    TODAY = "today"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
    LAST_3_MONTHS = "last_3_months"
