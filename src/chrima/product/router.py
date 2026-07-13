from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.deps import depends_db_sess, depends_workspace_id, depends_object
from chrima.api.schema import PaginatedResponse
from .schema import CreateProductRequest, ProductResponse, UpdateProductRequest
from .service.service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", status_code=201, response_model=ProductResponse)
async def create_product(
    body: CreateProductRequest,
    merchant_id: UUID = Depends(depends_workspace_id),
    db_sess: AsyncSession = Depends(depends_db_sess),
    product_service: ProductService = Depends(depends_object(ProductService)),
):
    return await product_service.create(
        workspace_id=merchant_id,
        name=body.name,
        description=body.description,
        wallet_id=body.wallet_id,
        external_url=body.external_url,
        roles=body.roles,
        fulfilment_type=body.fulfilment_type,
        price_data=body.price,
        db_sess=db_sess,
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    merchant_id: UUID = Depends(depends_workspace_id),
    db_sess: AsyncSession = Depends(depends_db_sess),
    product_service: ProductService = Depends(depends_object(ProductService)),
):
    return await product_service.get_by_workspace(product_id, merchant_id, db_sess)


@router.get("/", response_model=PaginatedResponse[ProductResponse])
async def list_products(
    page: int = Query(1, ge=1),
    limit: int = Query(1, ge=1, le=100),
    merchant_id: UUID = Depends(depends_workspace_id),
    db_sess: AsyncSession = Depends(depends_db_sess),
    product_service: ProductService = Depends(depends_object(ProductService)),
):
    return await product_service.list_by_workspace(merchant_id, page, limit, db_sess)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    body: UpdateProductRequest,
    merchant_id: UUID = Depends(depends_workspace_id),
    db_sess: AsyncSession = Depends(depends_db_sess),
    product_service: ProductService = Depends(depends_object(ProductService)),
):
    return await product_service.update(
        product_id,
        merchant_id,
        name=body.name,
        description=body.description,
        wallet_id=body.wallet_id,
        db_sess=db_sess,
    )


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: UUID,
    merchant_id: UUID = Depends(depends_workspace_id),
    db_sess: AsyncSession = Depends(depends_db_sess),
    product_service: ProductService = Depends(depends_object(ProductService)),
):
    await product_service.delete(product_id, merchant_id, db_sess)
