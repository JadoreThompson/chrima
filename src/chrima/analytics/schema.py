from core.schema import CustomBaseModel
from .enums import TimePeriod


class AnalyticsSummary(CustomBaseModel):
    total_revenue: float
    total_active_customers: int
    total_transactions: int


class TimeSeriesPoint(CustomBaseModel):
    label: str
    value: float


class AnalyticsTimeSeries(CustomBaseModel):
    period: TimePeriod
    points: list[TimeSeriesPoint]


class SubscriptionAnalytics(CustomBaseModel):
    active: int
    expired: int
    cancelled: int
    expiring: int
    """Active subscriptions whose cycle_end is within the next 7 days"""
