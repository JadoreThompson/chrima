from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.schema import PaginatedResponse

from .exception import MerchantNotFoundException
from .model import Merchant
from .schema import MerchantResponse


class MerchantService:

    def __init__(self):
        pass

    async def create_merchant(
        self, user_id: UUID, name: str, wallet_address: str, db_sess: AsyncSession
    ) -> MerchantResponse:
        merchant = Merchant(user_id=user_id, name=name, wallet_address=wallet_address)
        db_sess.add(merchant)
        await db_sess.flush()
        await db_sess.refresh(merchant)
        return self._create_merchant_response(merchant)

    async def get_merchant(
        self, merchant_id: UUID, db_sess: AsyncSession
    ) -> MerchantResponse:
        merchant = await db_sess.get(Merchant, merchant_id)
        if merchant is None:
            raise MerchantNotFoundException(merchant_id)
        return self._create_merchant_response(merchant)

    async def get_merchant_by_user_id(
        self, merchant_id: UUID, user_id: UUID, db_sess: AsyncSession
    ) -> MerchantResponse:
        merchant = await self._get_merchant(merchant_id, user_id, db_sess)
        return self._create_merchant_response(merchant)

    async def get_merchants_by_user(
        self, user_id: UUID, page: int, limit: int, db_sess: AsyncSession
    ) -> PaginatedResponse:
        offset = (page - 1) * limit

        result = await db_sess.execute(
            select(Merchant)
            .where(Merchant.user_id == user_id)
            .offset(offset)
            .limit(limit + 1)
        )

        rows = list(result.scalars().all())
        has_next = len(rows) > limit
        data = [self._create_merchant_response(m) for m in rows[:limit]]

        return PaginatedResponse(
            page=page,
            size=len(data),
            has_next=has_next,
            data=data,
        )

    async def update_merchant(
        self,
        merchant_id: UUID,
        user_id: UUID,
        name: str | None = None,
        wallet_address: str | None = None,
        *,
        db_sess: AsyncSession,
    ) -> MerchantResponse:
        merchant = await self._get_merchant(merchant_id, user_id, db_sess)

        if name is not None:
            merchant.name = name

        if wallet_address is not None:
            merchant.wallet_address = wallet_address

        return self._create_merchant_response(merchant)

    async def delete_merchant(
        self, merchant_id: UUID, user_id: UUID, db_sess: AsyncSession
    ) -> None:
        merchant = await self._get_merchant(merchant_id, user_id, db_sess)
        await db_sess.delete(merchant)

    async def _get_merchant(
        self, merchant_id: UUID, user_id: UUID, db_sess: AsyncSession
    ) -> Merchant:
        merchant = await db_sess.scalar(
            select(Merchant).where(
                Merchant.id == merchant_id, Merchant.user_id == user_id
            )
        )
        if merchant is None:
            raise MerchantNotFoundException(merchant_id)

        return merchant

    def _create_merchant_response(self, merchant: Merchant) -> MerchantResponse:
        return MerchantResponse(
            id=merchant.id,
            user_id=merchant.user_id,
            name=merchant.name,
            wallet_address=merchant.wallet_address,
            created_at=merchant.created_at,
            updated_at=merchant.updated_at,
        )
