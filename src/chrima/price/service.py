from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.schema import PaginatedResponse
from chrima.tokens import TokenService

from .enums import PriceType
from .exception import PriceNotFoundException
from .model import Price, PriceToken
from .schema import PriceResponse


class PriceService:

    def __init__(self, *, token_service: TokenService):
        self.token_service = token_service

    async def create_price(
        self,
        merchant_id: UUID,
        product_id: UUID,
        type: PriceType,
        currency: str,
        amount: float,
        active: bool,
        token_ids: list[UUID] | None = None,
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

        if token_ids:
            for tid in token_ids:
                db_sess.add(PriceToken(price_id=price.id, token_id=tid))

        return await self._create_price_response(price, db_sess)

    async def get_price(
        self, price_id: UUID, merchant_id: UUID, db_sess: AsyncSession
    ) -> PriceResponse:
        price = await self._get_price(price_id, merchant_id, db_sess)
        return await self._create_price_response(price, db_sess)
    
    async def get_price_by_id(self, price_id: UUID, db_sess: AsyncSession) -> PriceResponse:
        price = await db_sess.get(Price, price_id)
        
        if price is None:
            raise PriceNotFoundException(price_id)

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
        data = [await self._create_price_response(p, db_sess) for p in rows[:limit]]
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

        return await self._create_price_response(price, db_sess)

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

    async def _fetch_price_token_ids(
        self, price_id: UUID, db_sess: AsyncSession
    ) -> list[UUID]:
        result = await db_sess.execute(
            select(PriceToken.token_id).where(PriceToken.price_id == price_id)
        )
        return [row[0] for row in result.all()]

    async def _create_price_response(
        self, price: Price, db_sess: AsyncSession
    ) -> PriceResponse:
        token_ids = await self._fetch_price_token_ids(price.id, db_sess)
        tokens = []
        if token_ids:
            tokens = await self.token_service.get_tokens_by_ids(token_ids, db_sess)
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
            tokens=tokens,
            created_at=price.created_at,
            updated_at=price.updated_at,
        )
