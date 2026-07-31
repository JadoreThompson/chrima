from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy import case, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.price.model import Price
from chrima.product.model import Product
from chrima.subscription.enums import SubscriptionStatus
from chrima.subscription.model import SubscriptionBalance
from chrima.transaction.enums import TransactionStatus
from chrima.transaction.model import Transaction
from .enums import TimePeriod
from .schema import (
    AnalyticsSummary,
    AnalyticsTimeSeries,
    SubscriptionAnalytics,
    TimeSeriesPoint,
)


class AnalyticsService:
    async def get_summary(
        self, workspace_id: UUID, db_sess: AsyncSession
    ) -> AnalyticsSummary:
        total_revenue = await self._total_revenue(workspace_id, db_sess)
        total_active_customers = await self._total_active_customers(
            workspace_id, db_sess
        )
        total_transactions = await self._total_transactions(workspace_id, db_sess)
        return AnalyticsSummary(
            total_revenue=total_revenue,
            total_active_customers=total_active_customers,
            total_transactions=total_transactions,
        )

    async def get_revenue_timeseries(
        self, workspace_id: UUID, period: TimePeriod, db_sess: AsyncSession
    ) -> AnalyticsTimeSeries:
        start, end, labels = self._period_bounds(period)
        bucket_map = await self._query_buckets(
            workspace_id, start, end, period, db_sess, is_revenue=True
        )
        print("bucket map:", bucket_map, " labels:", labels)
        points = [
            TimeSeriesPoint(label=label, value=bucket_map.get(i, 0.0))
            for i, label in labels
        ]
        return AnalyticsTimeSeries(period=period, points=points)

    async def get_active_customers_timeseries(
        self, workspace_id: UUID, period: TimePeriod, db_sess: AsyncSession
    ) -> AnalyticsTimeSeries:
        start, end, labels = self._period_bounds(period)
        bucket_map = await self._query_buckets(
            workspace_id, start, end, period, db_sess, is_revenue=False
        )
        points = [
            TimeSeriesPoint(label=label, value=float(bucket_map.get(i, 0)))
            for i, label in labels
        ]
        return AnalyticsTimeSeries(period=period, points=points)

    def _period_bounds(
        self, period: TimePeriod
    ) -> tuple[int, int, list[tuple[int, str]]]:
        now = datetime.now(timezone.utc)
        now_ts = int(now.timestamp())

        if period == TimePeriod.TODAY:
            start = int(
                now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
            )
            labels = [(i, f"{i*8:02d}:00") for i in range(3)]
            return start, now_ts, labels

        if period == TimePeriod.THIS_WEEK:
            week_start = now - timedelta(days=now.weekday())
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            start = int(week_start.timestamp())
            labels = [
                (i, (week_start + timedelta(days=i)).strftime("%A")) for i in range(7)
            ]
            return start, now_ts, labels

        if period == TimePeriod.THIS_MONTH:
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            start = int(month_start.timestamp())
            labels = [(i, f"Week {i + 1}") for i in range(4)]
            return start, now_ts, labels

        three_months_ago = now.replace(day=1) - timedelta(days=89)
        three_months_ago = three_months_ago.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        start = int(three_months_ago.timestamp())
        labels = []
        for i in range(3):
            m = now.month - (2 - i)
            y = now.year
            if m <= 0:
                m += 12
                y -= 1
            dt = datetime(y, m, 1, tzinfo=timezone.utc)
            labels.append((m, dt.strftime("%B")))
        return start, now_ts, labels

    async def _query_buckets(
        self,
        workspace_id: UUID,
        start_ts: int,
        end_ts: int,
        period: TimePeriod,
        db_sess: AsyncSession,
        is_revenue: bool,
    ) -> dict[int, float]:
        bucket_expr = self._bucket_expression(period)
        value_expr = (
            func.sum(Transaction.amount)
            if is_revenue
            else func.count(func.distinct(Transaction.platform_user_id))
        )

        rows = await db_sess.execute(
            select(bucket_expr, value_expr.label("v"))
            .select_from(Transaction)
            .join(Price, Transaction.price_id == Price.id)
            .where(Price.workspace_id == workspace_id)
            .where(Transaction.status == TransactionStatus.COMPLETE)
            .where(Transaction.timestamp >= start_ts)
            .where(Transaction.timestamp < end_ts)
            .group_by(text("bucket"))
            .order_by(text("bucket"))
        )
        return {
            row[0]: float(row[1]) if row[1] is not None else 0.0 for row in rows.all()
        }

    def _bucket_expression(self, period: TimePeriod):
        ts = func.to_timestamp(Transaction.timestamp)
        if period == TimePeriod.TODAY:
            return func.floor(func.extract("hour", ts) / 8).label("bucket")
        if period == TimePeriod.THIS_WEEK:
            return func.floor((func.extract("dow", ts) + 6) % 7).label("bucket")
        if period == TimePeriod.THIS_MONTH:
            # return func.floor(func.extract("day", ts) / 7).label("bucket")
            day = func.extract("day", ts)
            return func.least(func.floor((day - 1) / 7), 3).label("bucket")
        return func.extract("month", ts).label("bucket")

    async def _total_revenue(self, workspace_id: UUID, db_sess: AsyncSession) -> float:
        result = await db_sess.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .select_from(Transaction)
            .join(Price, Transaction.price_id == Price.id)
            .where(Price.workspace_id == workspace_id)
            .where(Transaction.status == TransactionStatus.COMPLETE)
        )
        return float(result.scalar())

    async def _total_active_customers(
        self, workspace_id: UUID, db_sess: AsyncSession
    ) -> int:
        result = await db_sess.execute(
            select(func.count(func.distinct(SubscriptionBalance.platform_user_id)))
            .select_from(SubscriptionBalance)
            .join(Product, SubscriptionBalance.product_id == Product.id)
            .where(Product.workspace_id == workspace_id)
            .where(SubscriptionBalance.status == SubscriptionStatus.ACTIVE)
        )
        return result.scalar()

    async def get_subscription_breakdown(
        self, workspace_id: UUID, db_sess: AsyncSession
    ) -> SubscriptionAnalytics:
        now_ts = int(datetime.now(timezone.utc).timestamp())
        expiring_threshold = now_ts + 7 * 86400

        is_expiring = case(
            (
                (SubscriptionBalance.status == SubscriptionStatus.ACTIVE)
                & SubscriptionBalance.cycle_end.isnot(None)
                & (SubscriptionBalance.cycle_end <= expiring_threshold),
                1,
            ),
            else_=0,
        )

        row = await db_sess.execute(
            select(
                func.sum(
                    case(
                        (SubscriptionBalance.status == SubscriptionStatus.ACTIVE, 1),
                        else_=0,
                    )
                ).label("active"),
                func.sum(
                    case(
                        (SubscriptionBalance.status == SubscriptionStatus.EXPIRED, 1),
                        else_=0,
                    )
                ).label("expired"),
                func.sum(
                    case(
                        (SubscriptionBalance.status == SubscriptionStatus.CANCELLED, 1),
                        else_=0,
                    )
                ).label("cancelled"),
                func.sum(is_expiring).label("expiring"),
            )
            .select_from(SubscriptionBalance)
            .join(Product, SubscriptionBalance.product_id == Product.id)
            .where(Product.workspace_id == workspace_id)
        )
        r = row.one()
        return SubscriptionAnalytics(
            active=r.active or 0,
            expired=r.expired or 0,
            cancelled=r.cancelled or 0,
            expiring=r.expiring or 0,
        )

    async def _total_transactions(
        self, workspace_id: UUID, db_sess: AsyncSession
    ) -> int:
        result = await db_sess.execute(
            select(func.count(Transaction.id))
            .select_from(Transaction)
            .join(Price, Transaction.price_id == Price.id)
            .where(Price.workspace_id == workspace_id)
            .where(Transaction.status == TransactionStatus.COMPLETE)
        )
        return result.scalar()
