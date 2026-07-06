from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.deps import depends_db_sess, depends_workspace_id, depends_object
from chrima.api.schema import PaginatedResponse
from .schema import CreateWalletRequest, WalletResponse
from .service import WalletService

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.post("/", status_code=201, response_model=WalletResponse)
async def create_wallet(
    body: CreateWalletRequest,
    workspace_id: UUID = Depends(depends_workspace_id),
    db_sess: AsyncSession = Depends(depends_db_sess),
    wallet_service: WalletService = Depends(depends_object(WalletService)),
):
    return await wallet_service.create(
        workspace_id=workspace_id,
        name=body.name,
        wallet_address=body.wallet_address,
        token_ids=body.token_ids,
        db_sess=db_sess,
    )


@router.get("/{wallet_id}", response_model=WalletResponse)
async def get_wallet(
    wallet_id: UUID,
    workspace_id: UUID = Depends(depends_workspace_id),
    db_sess: AsyncSession = Depends(depends_db_sess),
    wallet_service: WalletService = Depends(depends_object(WalletService)),
):
    return await wallet_service.get(wallet_id, workspace_id, db_sess)


@router.get("/", response_model=PaginatedResponse[WalletResponse])
async def list_wallets(
    page: int = Query(1, ge=1),
    limit: int = Query(1, ge=1, le=100),
    workspace_id: UUID = Depends(depends_workspace_id),
    db_sess: AsyncSession = Depends(depends_db_sess),
    wallet_service: WalletService = Depends(depends_object(WalletService)),
):
    return await wallet_service.list_by_workspace(workspace_id, page, limit, db_sess)


@router.delete("/{wallet_id}", status_code=204)
async def delete_wallet(
    wallet_id: UUID,
    workspace_id: UUID = Depends(depends_workspace_id),
    db_sess: AsyncSession = Depends(depends_db_sess),
    wallet_service: WalletService = Depends(depends_object(WalletService)),
):
    await wallet_service.delete(wallet_id, workspace_id, db_sess)
