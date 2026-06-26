from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.deps import depends_db_sess, depends_jwt, depends_object
from chrima.api.schema import PaginatedResponse
from chrima.jwt.schema import JWTPayload
from .schema import (
    CreateMerchantRequest,
    MerchantResponse,
    UpdateMerchantRequest,
)
from .service import MerchantService

router = APIRouter(prefix="/merchants", tags=["merchants"])


@router.post("/", status_code=201, response_model=MerchantResponse)
async def create_merchant(
    body: CreateMerchantRequest,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    merchant_service: MerchantService = Depends(depends_object(MerchantService)),
):
    return await merchant_service.create_merchant(
        user_id=jwt.sub,
        name=body.name,
        wallet_address=body.wallet_address,
        db_sess=db_sess,
    )


@router.get("/{merchant_id}", response_model=MerchantResponse)
async def get_merchant(
    merchant_id: UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    merchant_service: MerchantService = Depends(depends_object(MerchantService)),
):
    return await merchant_service.get_merchant_by_user_id(merchant_id, jwt.sub, db_sess)


@router.get("/", response_model=PaginatedResponse[MerchantResponse])
async def list_merchants(
    page: int = Query(1, ge=1),
    limit: int = Query(1, ge=1, le=100),
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    merchant_service: MerchantService = Depends(depends_object(MerchantService)),
):
    return await merchant_service.get_merchants_by_user(jwt.sub, page, limit, db_sess)


@router.patch("/{merchant_id}", response_model=MerchantResponse)
async def update_merchant(
    merchant_id: UUID,
    request: UpdateMerchantRequest,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    merchant_service: MerchantService = Depends(depends_object(MerchantService)),
):
    return await merchant_service.update_merchant(
        merchant_id,
        user_id=jwt.sub,
        name=request.name,
        wallet_address=request.wallet_address,
        db_sess=db_sess,
    )


@router.delete("/{merchant_id}", status_code=204)
async def delete_merchant(
    merchant_id: UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    merchant_service: MerchantService = Depends(depends_object(MerchantService)),
):
    await merchant_service.delete_merchant(merchant_id, jwt.sub, db_sess)
