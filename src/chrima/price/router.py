from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.deps import (
    depends_db_sess,
    depends_jwt,
    depends_object,
)
from chrima.api.schema import PaginatedResponse
from chrima.jwt.schema import JWTPayload
from chrima.product import ProductService
from chrima.workspace import WorkspaceService
from .schema import CreatePriceRequest, PriceResponse, UpdatePriceRequest
from .service.price import PriceService

router = APIRouter(prefix="/prices", tags=["prices"])


@router.post("/", status_code=201, response_model=PriceResponse)
async def create_price(
    body: CreatePriceRequest,
    db_sess: AsyncSession = Depends(depends_db_sess),
    jwt: JWTPayload = Depends(depends_jwt),
    price_service: PriceService = Depends(depends_object(PriceService)),
    workspace_service: WorkspaceService = Depends(depends_object(WorkspaceService)),
):
    workspace = await workspace_service.get(body.workspace_id, jwt.sub, db_sess)
    return await price_service.create(
        workspace_id=workspace.id,
        product_id=body.product_id,
        type=body.type,
        currency=body.currency,
        amount=body.amount,
        active=body.active,
        recurring_interval=body.recurring_interval,
        recurring_interval_count=body.recurring_interval_count,
        trial_period_days=body.trial_period_days,
        db_sess=db_sess,
    )


@router.get("/{price_id}", response_model=PriceResponse)
async def get_price(
    price_id: UUID,
    db_sess: AsyncSession = Depends(depends_db_sess),
    price_service: PriceService = Depends(depends_object(PriceService)),
):
    return await price_service.get_by_id(price_id, db_sess)


@router.get("/", response_model=PaginatedResponse[PriceResponse])
async def list_prices(
    product_id: UUID = Query(),
    page: int = Query(1, ge=1),
    limit: int = Query(1, ge=1, le=100),
    db_sess: AsyncSession = Depends(depends_db_sess),
    product_service: ProductService = Depends(depends_object(ProductService)),
    price_service: PriceService = Depends(depends_object(PriceService)),
):
    product = await product_service.get_by_id(product_id, db_sess)
    return await price_service.list_by_product(product.id, page, limit, db_sess)


@router.patch("/{price_id}", response_model=PriceResponse)
async def update_price(
    price_id: UUID,
    body: UpdatePriceRequest,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    price_service: PriceService = Depends(depends_object(PriceService)),
    workspace_service: WorkspaceService = Depends(depends_object(WorkspaceService)),
):
    price = await price_service.get_by_id(price_id, db_sess)
    workspace = await workspace_service.get(price.workspace_id, jwt.sub, db_sess)
    return await price_service.update(
        price_id,
        workspace.id,
        currency=body.currency,
        amount=body.amount,
        recurring_interval=body.recurring_interval,
        recurring_interval_count=body.recurring_interval_count,
        trial_period_days=body.trial_period_days,
        active=body.active,
        db_sess=db_sess,
    )


@router.delete("/{price_id}", status_code=204)
async def delete_price(
    price_id: UUID,
    db_sess: AsyncSession = Depends(depends_db_sess),
    jwt: JWTPayload = Depends(depends_jwt),
    price_service: PriceService = Depends(depends_object(PriceService)),
    workspace_service: WorkspaceService = Depends(depends_object(WorkspaceService)),
):
    price = await price_service.get_by_id(price_id, db_sess)
    workspace = await workspace_service.get(price.workspace_id, jwt.sub, db_sess)
    await price_service.delete(price_id, workspace.id, db_sess=db_sess)
