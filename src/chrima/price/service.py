from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.schema import PaginatedResponse

from .enums import PriceType
from .exception import PriceNotFoundException
from .model import Price
from .schema import PriceResponse


class PriceService:

    def __init__(self):
        pass

    async def create_price(
        self,
        merchant_id: UUID,
        product_id: UUID,
        type: PriceType,
        currency: str,
        amount: float,
        active: bool,
        recurring_interval: str | None = None,
        recurring_interval_count: int | None = None,
        trial_period_days: int | None = None,
        db_sess: AsyncSession = None,
    ) -> PriceResponse:
        price = Price(
            merchant_id=merchant_id,
            product_id=product_id,
            type=type,
            currency=currency,
            amount=amount,
            active=active,
            recurring_interval=recurring_interval,
            recurring_interval_count=recurring_interval_count,
            trial_period_days=trial_period_days,
        )
        db_sess.add(price)
        await db_sess.flush()
        await db_sess.refresh(price)
        return self._create_price_response(price)

    async def get_price(
        self, price_id: UUID, merchant_id: UUID, db_sess: AsyncSession
    ) -> PriceResponse:
        price = await self._get_price(price_id, merchant_id, db_sess)
        return self._create_price_response(price)

    async def get_prices_by_product(
        self,
        product_id: UUID,
        merchant_id: UUID,
        page: int,
        limit: int,
        db_sess: AsyncSession,
    ) -> PaginatedResponse:
        offset = (page - 1) * limit
        result = await db_sess.execute(
            select(Price)
            .where(Price.product_id == product_id, Price.merchant_id == merchant_id)
            .offset(offset)
            .limit(limit + 1)
        )
        rows = list(result.scalars().all())
        has_next = len(rows) > limit
        data = [self._create_price_response(p) for p in rows[:limit]]
        return PaginatedResponse(
            page=page,
            size=len(data),
            has_next=has_next,
            data=data,
        )

    async def update_price(
        self,
        price_id: UUID,
        merchant_id: UUID,
        currency: str | None = None,
        amount: float | None = None,
        recurring_interval: str | None = None,
        recurring_interval_count: int | None = None,
        trial_period_days: int | None = None,
        active: bool | None = None,
        *,
        db_sess: AsyncSession,
    ) -> PriceResponse:
        price = await self._get_price(price_id, merchant_id, db_sess)

        if currency is not None:
            price.currency = currency
        if amount is not None:
            price.amount = amount
        if recurring_interval is not None:
            price.recurring_interval = recurring_interval
        if recurring_interval_count is not None:
            price.recurring_interval_count = recurring_interval_count
        if trial_period_days is not None:
            price.trial_period_days = trial_period_days
        if active is not None:
            price.active = active

        return self._create_price_response(price)

    async def delete_price(
        self, price_id: UUID, merchant_id: UUID, db_sess: AsyncSession
    ) -> None:
        price = await self._get_price(price_id, merchant_id, db_sess)
        await db_sess.delete(price)

    async def _get_price(
        self, price_id: UUID, merchant_id: UUID, db_sess: AsyncSession
    ):
        price = await db_sess.scalar(
            select(Price).where(Price.id == price_id, Price.merchant_id == merchant_id)
        )
        if price is None:
            raise PriceNotFoundException(price_id)
        return price

    def _create_price_response(self, price: Price) -> PriceResponse:
        return PriceResponse(
            id=price.id,
            merchant_id=price.merchant_id,
            product_id=price.product_id,
            type=price.type,
            currency=price.currency,
            amount=price.amount,
            recurring_interval=price.recurring_interval,
            recurring_interval_count=price.recurring_interval_count,
            trial_period_days=price.trial_period_days,
            active=price.active,
            created_at=price.created_at,
            updated_at=price.updated_at,
        )
