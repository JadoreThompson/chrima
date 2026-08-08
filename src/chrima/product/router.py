import logging
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
from chrima.workspace import WorkspaceService
from .schema import CreateProductRequest, ProductResponse, UpdateProductRequest
from .service.product import ProductService

router = APIRouter(prefix="/products", tags=["products"])
logger = logging.getLogger("product_router")

@router.post("/", status_code=201, response_model=ProductResponse)
async def create_product(
    body: CreateProductRequest,
    db_sess: AsyncSession = Depends(depends_db_sess),
    jwt: JWTPayload = Depends(depends_jwt),
    product_service: ProductService = Depends(depends_object(ProductService)),
    workspace_service: WorkspaceService = Depends(depends_object(WorkspaceService)),
):
    workspace = await workspace_service.get(body.workspace_id, jwt.sub, db_sess)
    product = await product_service.create(
        workspace_id=workspace.id,
        name=body.name,
        description=body.description,
        wallet_id=body.wallet_id,
        external_url=body.external_url,
        roles=body.roles,
        fulfilment_type=body.fulfilment_type,
        db_sess=db_sess,
    )

    await db_sess.commit()

    return product


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db_sess: AsyncSession = Depends(depends_db_sess),
    product_service: ProductService = Depends(depends_object(ProductService)),
):
    return await product_service.get_by_id(product_id, db_sess)


@router.get("/", response_model=PaginatedResponse[ProductResponse])
async def list_products(
    page: int = Query(1, ge=1),
    limit: int = Query(1, ge=1, le=100),
    workspace_id: UUID = Query(),
    db_sess: AsyncSession = Depends(depends_db_sess),
    product_service: ProductService = Depends(depends_object(ProductService)),
    workspace_service: WorkspaceService = Depends(depends_object(WorkspaceService)),
):
    
    workspace = await workspace_service.get_by_id(workspace_id, db_sess)
    return await product_service.list_by_workspace(workspace.id, page, limit, db_sess)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    body: UpdateProductRequest,
    db_sess: AsyncSession = Depends(depends_db_sess),
    jwt: JWTPayload = Depends(depends_jwt),
    product_service: ProductService = Depends(depends_object(ProductService)),
    workspace_service: WorkspaceService = Depends(depends_object(WorkspaceService)),
):
    product = await product_service.get_by_id(product_id, db_sess)
    workspace = await workspace_service.get(product.workspace_id, jwt.sub, db_sess)
    product = await product_service.update(
        product.id,
        workspace.id,
        name=body.name,
        description=body.description,
        wallet_id=body.wallet_id,
        db_sess=db_sess,
    )
    await db_sess.commit()
    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: UUID,
    db_sess: AsyncSession = Depends(depends_db_sess),
    jwt: JWTPayload = Depends(depends_jwt),
    product_service: ProductService = Depends(depends_object(ProductService)),
    workspace_service: WorkspaceService = Depends(depends_object(WorkspaceService)),
):
    product = await product_service.get_by_id(product_id, db_sess)
    workspace = await workspace_service.get(product.workspace_id, jwt.sub, db_sess)
    await product_service.delete(product.id, workspace.id, db_sess)
    await db_sess.commit()
