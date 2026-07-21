from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.deps import depends_db_sess, depends_jwt, depends_object
from chrima.api.schema import PaginatedResponse
from chrima.jwt.schema import JWTPayload
from chrima.workspace import WorkspaceService
from .schema import CreateWalletRequest, WalletResponse
from .service import WalletService

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.post("/", status_code=201, response_model=WalletResponse)
async def create_wallet(
    body: CreateWalletRequest,
    db_sess: AsyncSession = Depends(depends_db_sess),
    jwt: JWTPayload = Depends(depends_jwt),
    wallet_service: WalletService = Depends(depends_object(WalletService)),
    workspace_service: WorkspaceService = Depends(depends_object(WorkspaceService)),
):
    workspace = await workspace_service.get(body.workspace_id, jwt.sub, db_sess)
    return await wallet_service.create(
        workspace_id=workspace.id,
        name=body.name,
        wallet_address=body.wallet_address,
        token_ids=body.token_ids,
        db_sess=db_sess,
    )


@router.get("/{wallet_id}", response_model=WalletResponse)
async def get_wallet(
    wallet_id: UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    wallet_service: WalletService = Depends(depends_object(WalletService)),
):
    return await wallet_service.get_by_id(wallet_id, db_sess)


@router.get("/", response_model=PaginatedResponse[WalletResponse])
async def list_wallets(
    page: int = Query(1, ge=1),
    limit: int = Query(1, ge=1, le=100),
    jwt: JWTPayload = Depends(depends_jwt),
    workspace_id: UUID = Query(),
    db_sess: AsyncSession = Depends(depends_db_sess),
    wallet_service: WalletService = Depends(depends_object(WalletService)),
    workspace_service: WorkspaceService = Depends(depends_object(WorkspaceService)),
):
    workspace = await workspace_service.get(workspace_id, jwt.sub, db_sess)
    return await wallet_service.list_by_workspace(workspace.id, page, limit, db_sess)


@router.delete("/{wallet_id}", status_code=204)
async def delete_wallet(
    wallet_id: UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    wallet_service: WalletService = Depends(depends_object(WalletService)),
    workspace_service: WorkspaceService = Depends(depends_object(WorkspaceService)),
):
    wallet = await wallet_service.get_by_id(wallet_id, db_sess)
    workspace = await workspace_service.get(wallet.workspace_id, jwt.sub, db_sess)
    await wallet_service.delete(wallet_id, workspace.id, db_sess)
