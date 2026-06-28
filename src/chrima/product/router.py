from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.deps import depends_db_sess, depends_merchant_id, depends_object
from chrima.api.schema import PaginatedResponse
from .schema import CreateProductRequest, ProductResponse, UpdateProductRequest
from .service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", status_code=201, response_model=ProductResponse)
async def create_product(
    body: CreateProductRequest,
    merchant_id: UUID = Depends(depends_merchant_id),
    db_sess: AsyncSession = Depends(depends_db_sess),
    product_service: ProductService = Depends(depends_object(ProductService)),
):
    return await product_service.create_product(
        merchant_id=merchant_id,
        name=body.name,
        description=body.description,
        wallet_id=body.wallet_id,
        group_type=body.group_type,
        group_url=body.group_url,
        group_id=body.group_id,
        roles=body.roles,
        access_type=body.access_type,
        price_data=body.price.model_dump(),
        db_sess=db_sess,
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    merchant_id: UUID = Depends(depends_merchant_id),
    db_sess: AsyncSession = Depends(depends_db_sess),
    product_service: ProductService = Depends(depends_object(ProductService)),
):
    return await product_service.get_product_by_merchant(product_id, merchant_id, db_sess)


@router.get("/", response_model=PaginatedResponse[ProductResponse])
async def list_products(
    page: int = Query(1, ge=1),
    limit: int = Query(1, ge=1, le=100),
    merchant_id: UUID = Depends(depends_merchant_id),
    db_sess: AsyncSession = Depends(depends_db_sess),
    product_service: ProductService = Depends(depends_object(ProductService)),
):
    return await product_service.get_products_by_merchant(merchant_id, page, limit, db_sess)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    body: UpdateProductRequest,
    merchant_id: UUID = Depends(depends_merchant_id),
    db_sess: AsyncSession = Depends(depends_db_sess),
    product_service: ProductService = Depends(depends_object(ProductService)),
):
    return await product_service.update_product(
        product_id,
        merchant_id,
        name=body.name,
        description=body.description,
        db_sess=db_sess,
    )


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: UUID,
    merchant_id: UUID = Depends(depends_merchant_id),
    db_sess: AsyncSession = Depends(depends_db_sess),
    product_service: ProductService = Depends(depends_object(ProductService)),
):
    await product_service.delete_product(product_id, merchant_id, db_sess)
