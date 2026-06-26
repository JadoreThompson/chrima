from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.deps import depends_db_sess, depends_merchant_id, depends_object
from chrima.api.schema import PaginatedResponse
from .schema import CreateWalletRequest, WalletResponse
from .service import MerchantWalletService

router = APIRouter(prefix="/merchants/wallets", tags=["merchant-wallets"])


@router.post("/", status_code=201, response_model=WalletResponse)
async def create_wallet(
    body: CreateWalletRequest,
    db_sess: AsyncSession = Depends(depends_db_sess),
    wallet_service: MerchantWalletService = Depends(
        depends_object(MerchantWalletService)
    ),
):
    return await wallet_service.create_wallet(
        merchant_id=body.merchant_id,
        name=body.name,
        wallet_address=body.wallet_address,
        token_ids=body.token_ids,
        db_sess=db_sess,
    )


@router.get("/{wallet_id}", response_model=WalletResponse)
async def get_wallet(
    wallet_id: UUID,
    merchant_id: UUID = Depends(depends_merchant_id),
    db_sess: AsyncSession = Depends(depends_db_sess),
    wallet_service: MerchantWalletService = Depends(
        depends_object(MerchantWalletService)
    ),
):
    return await wallet_service.get_wallet_by_merchant(wallet_id, merchant_id, db_sess)


@router.get("/", response_model=PaginatedResponse[WalletResponse])
async def list_wallets(
    page: int = Query(1, ge=1),
    limit: int = Query(1, ge=1, le=100),
    merchant_id: UUID = Depends(depends_merchant_id),
    db_sess: AsyncSession = Depends(depends_db_sess),
    wallet_service: MerchantWalletService = Depends(
        depends_object(MerchantWalletService)
    ),
):
    return await wallet_service.get_wallets_by_merchant(
        merchant_id, page, limit, db_sess
    )


@router.delete("/{wallet_id}", status_code=204)
async def delete_wallet(
    wallet_id: UUID,
    merchant_id: UUID = Depends(depends_merchant_id),
    db_sess: AsyncSession = Depends(depends_db_sess),
    wallet_service: MerchantWalletService = Depends(
        depends_object(MerchantWalletService)
    ),
):
    await wallet_service.delete_wallet(wallet_id, merchant_id, db_sess)
