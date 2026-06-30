from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.schema import PaginatedResponse
from chrima.product.model import Product

from ..model import WorkspaceWallet, WorkspaceWalletTokens
from .exception import WalletNotFoundException, WalletInUseException
from .schema import WalletResponse


class WorkspaceWalletService:
    def __init__(self):
        pass

    async def create(
        self,
        workspace_id: UUID,
        name: str,
        wallet_address: str,
        token_ids: list[UUID],
        db_sess: AsyncSession,
    ) -> WalletResponse:
        wallet = WorkspaceWallet(
            workspace_id=workspace_id,
            name=name,
            wallet_address=wallet_address,
        )
        db_sess.add(wallet)
        await db_sess.flush()
        await db_sess.refresh(wallet)

        for token_id in token_ids:
            db_sess.add(WorkspaceWalletTokens(wallet_id=wallet.id, token_id=token_id))

        return self._create_response(wallet, list(token_ids))

    async def _fetch_token_ids(
        self, wallet_id: UUID, db_sess: AsyncSession
    ) -> list[UUID]:
        result = await db_sess.execute(
            select(WorkspaceWalletTokens.token_id).where(
                WorkspaceWalletTokens.wallet_id == wallet_id
            )
        )
        return [row[0] for row in result.all()]

    async def get_by_id(self, wallet_id: UUID, db_sess: AsyncSession) -> WalletResponse:
        wallet = await db_sess.get(WorkspaceWallet, wallet_id)
        if wallet is None:
            raise WalletNotFoundException(wallet_id)
        token_ids = await self._fetch_token_ids(wallet_id, db_sess)
        return self._create_response(wallet, token_ids)

    async def get(
        self, wallet_id: UUID, workspace_id: UUID, db_sess: AsyncSession
    ) -> WalletResponse:
        wallet = await db_sess.scalar(
            select(WorkspaceWallet).where(
                WorkspaceWallet.id == wallet_id,
                WorkspaceWallet.workspace_id == workspace_id,
            )
        )
        if wallet is None:
            raise WalletNotFoundException(wallet_id)
        token_ids = await self._fetch_token_ids(wallet_id, db_sess)
        return self._create_response(wallet, token_ids)

    async def get_by_workspace(
        self, workspace_id: UUID, page: int, limit: int, db_sess: AsyncSession
    ) -> PaginatedResponse:
        offset = (page - 1) * limit
        result = await db_sess.execute(
            select(WorkspaceWallet)
            .where(WorkspaceWallet.workspace_id == workspace_id)
            .offset(offset)
            .limit(limit + 1)
        )
        rows = list(result.scalars().all())
        has_next = len(rows) > limit

        data = []
        for w in rows[:limit]:
            token_ids = await self._fetch_token_ids(w.id, db_sess)
            data.append(self._create_response(w, token_ids))

        return PaginatedResponse(
            page=page,
            size=len(data),
            has_next=has_next,
            data=data,
        )

    async def delete(
        self, wallet_id: UUID, workspace_id: UUID, db_sess: AsyncSession
    ) -> None:
        wallet = await db_sess.get(WorkspaceWallet, wallet_id)
        if wallet is None or wallet.workspace_id != workspace_id:
            raise WalletNotFoundException(wallet_id)

        product = await db_sess.scalar(
            select(Product).where(Product.wallet_id == wallet_id).limit(1)
        )
        if product is not None:
            raise WalletInUseException(wallet_id)

        await db_sess.delete(wallet)

    def _create_response(
        self, wallet: WorkspaceWallet, token_ids: list[UUID]
    ) -> WalletResponse:
        return WalletResponse(
            id=wallet.id,
            workspace_id=wallet.workspace_id,
            name=wallet.name,
            wallet_address=wallet.wallet_address,
            token_ids=token_ids,
            created_at=wallet.created_at,
        )
