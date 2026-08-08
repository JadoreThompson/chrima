from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.schema import PaginatedResponse
from chrima.product.model import Product
from .model import Wallet, WalletTokens
from .exception import WalletNotFoundException, WalletInUseException
from .schema import WalletResponse


class WalletService:
    async def create(
        self,
        workspace_id: UUID,
        name: str,
        wallet_address: str,
        db_sess: AsyncSession,
    ) -> WalletResponse:
        # TODO: Add validation that the wallet address exists
        wallet = Wallet(
            workspace_id=workspace_id,
            name=name,
            wallet_address=wallet_address,
        )
        db_sess.add(wallet)
        await db_sess.flush()
        await db_sess.refresh(wallet)

        return self._create_response(wallet)

    async def _fetch_token_ids(
        self, wallet_id: UUID, db_sess: AsyncSession
    ) -> list[UUID]:
        result = await db_sess.execute(
            select(WalletTokens.token_id).where(WalletTokens.wallet_id == wallet_id)
        )
        return result.scalars().all()

    async def get_by_id(self, wallet_id: UUID, db_sess: AsyncSession) -> WalletResponse:
        wallet = await db_sess.get(Wallet, wallet_id)
        if wallet is None:
            raise WalletNotFoundException(wallet_id)
        return self._create_response(wallet)

    async def get(
        self, wallet_id: UUID, workspace_id: UUID, db_sess: AsyncSession
    ) -> WalletResponse:
        wallet = await db_sess.scalar(
            select(Wallet).where(
                Wallet.id == wallet_id,
                Wallet.workspace_id == workspace_id,
            )
        )
        if wallet is None:
            raise WalletNotFoundException(wallet_id)
        return self._create_response(wallet)

    async def list_by_workspace(
        self, workspace_id: UUID, page: int, limit: int, db_sess: AsyncSession
    ) -> PaginatedResponse[WalletResponse]:
        offset = (page - 1) * limit
        result = await db_sess.execute(
            select(Wallet)
            .where(Wallet.workspace_id == workspace_id)
            .offset(offset)
            .limit(limit + 1)
        )
        rows = list(result.scalars().all())
        has_next = len(rows) > limit

        data = [self._create_response(w) for w in rows[:limit]]

        return PaginatedResponse(
            page=page,
            size=len(data),
            has_next=has_next,
            data=data,
        )

    async def delete(
        self, wallet_id: UUID, workspace_id: UUID, db_sess: AsyncSession
    ) -> None:
        wallet = await db_sess.get(Wallet, wallet_id)
        if wallet is None or wallet.workspace_id != workspace_id:
            raise WalletNotFoundException(wallet_id)

        product = await db_sess.scalar(
            select(Product).where(Product.wallet_id == wallet_id).limit(1)
        )
        if product is not None:
            raise WalletInUseException(wallet_id)

        await db_sess.delete(wallet)

    def _create_response(self, wallet: Wallet) -> WalletResponse:
        return WalletResponse(
            id=wallet.id,
            workspace_id=wallet.workspace_id,
            name=wallet.name,
            wallet_address=wallet.wallet_address,
            created_at=wallet.created_at,
        )
