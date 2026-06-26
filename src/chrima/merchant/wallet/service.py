from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.schema import PaginatedResponse
from chrima.product.model import Product

from ..model import MerchantWallet, MerchantWalletTokens
from .exception import WalletNotFoundException, WalletInUseException
from .schema import WalletResponse


class MerchantWalletService:

    def __init__(self):
        pass

    async def create_wallet(
        self,
        merchant_id: UUID,
        name: str,
        wallet_address: str,
        token_ids: list[UUID],
        db_sess: AsyncSession,
    ) -> WalletResponse:
        wallet = MerchantWallet(
            merchant_id=merchant_id,
            name=name,
            wallet_address=wallet_address,
        )
        db_sess.add(wallet)
        await db_sess.flush()
        await db_sess.refresh(wallet)

        for token_id in token_ids:
            db_sess.add(MerchantWalletTokens(wallet_id=wallet.id, token_id=token_id))

        return self._create_wallet_response(wallet, list(token_ids))

    async def _fetch_token_ids(self, wallet_id: UUID, db_sess: AsyncSession) -> list[UUID]:
        result = await db_sess.execute(
            select(MerchantWalletTokens.token_id).where(
                MerchantWalletTokens.wallet_id == wallet_id
            )
        )
        return [row[0] for row in result.all()]

    async def get_wallet(
        self, wallet_id: UUID, db_sess: AsyncSession
    ) -> WalletResponse:
        wallet = await db_sess.get(MerchantWallet, wallet_id)
        if wallet is None:
            raise WalletNotFoundException(wallet_id)
        token_ids = await self._fetch_token_ids(wallet_id, db_sess)
        return self._create_wallet_response(wallet, token_ids)

    async def get_wallet_by_merchant(
        self, wallet_id: UUID, merchant_id: UUID, db_sess: AsyncSession
    ) -> WalletResponse:
        wallet = await db_sess.scalar(
            select(MerchantWallet).where(
                MerchantWallet.id == wallet_id,
                MerchantWallet.merchant_id == merchant_id,
            )
        )
        if wallet is None:
            raise WalletNotFoundException(wallet_id)
        token_ids = await self._fetch_token_ids(wallet_id, db_sess)
        return self._create_wallet_response(wallet, token_ids)

    async def get_wallets_by_merchant(
        self, merchant_id: UUID, page: int, limit: int, db_sess: AsyncSession
    ) -> PaginatedResponse:
        offset = (page - 1) * limit
        result = await db_sess.execute(
            select(MerchantWallet)
            .where(MerchantWallet.merchant_id == merchant_id)
            .offset(offset)
            .limit(limit + 1)
        )
        rows = list(result.scalars().all())
        has_next = len(rows) > limit

        data = []
        for w in rows[:limit]:
            token_ids = await self._fetch_token_ids(w.id, db_sess)
            data.append(self._create_wallet_response(w, token_ids))

        return PaginatedResponse(
            page=page,
            size=len(data),
            has_next=has_next,
            data=data,
        )

    async def delete_wallet(
        self, wallet_id: UUID, merchant_id: UUID, db_sess: AsyncSession
    ) -> None:
        wallet = await db_sess.get(MerchantWallet, wallet_id)
        if wallet is None or wallet.merchant_id != merchant_id:
            raise WalletNotFoundException(wallet_id)

        product = await db_sess.scalar(
            select(Product).where(Product.wallet_id == wallet_id).limit(1)
        )
        if product is not None:
            raise WalletInUseException(wallet_id)

        await db_sess.execute(
            select(MerchantWalletTokens).where(
                MerchantWalletTokens.wallet_id == wallet_id
            )
        )
        await db_sess.execute(
            MerchantWalletTokens.__table__.delete().where(
                MerchantWalletTokens.wallet_id == wallet_id
            )
        )
        await db_sess.delete(wallet)

    def _create_wallet_response(self, wallet: MerchantWallet, token_ids: list[UUID]) -> WalletResponse:
        return WalletResponse(
            id=wallet.id,
            merchant_id=wallet.merchant_id,
            name=wallet.name,
            wallet_address=wallet.wallet_address,
            token_ids=token_ids,
            created_at=wallet.created_at,
        )
