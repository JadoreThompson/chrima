from enum import Enum


class TimePeriod(str, Enum):
    TODAY = "today"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
