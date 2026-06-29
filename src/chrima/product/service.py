from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.schema import PaginatedResponse
from chrima.price.service import PriceService

from .enums import FulfilmentType
from .exception import ProductNotFoundException
from .model import Product
from .schema import CreatePriceRequest, ProductResponse


class ProductService:
    def __init__(self, *, price_service: PriceService):
        self.price_service = price_service

    async def create_product(
        self,
        merchant_id: UUID,
        name: str,
        description: str | None,
        wallet_id: UUID,
        external_url: str | None,
        roles: list[str] | None,
        fulfilment_type: FulfilmentType,
        price_data: CreatePriceRequest,
        db_sess: AsyncSession,
    ) -> ProductResponse:
        product = Product(
            merchant_id=merchant_id,
            name=name,
            description=description,
            wallet_id=wallet_id,
            external_url=external_url,
            roles=roles,
            fulfilment_type=fulfilment_type,
        )
        db_sess.add(product)
        
        await db_sess.flush()
        await db_sess.refresh(product)

        price = await self.price_service.create_price(
            merchant_id=merchant_id,
            product_id=product.id,
            type=price_data.type,
            currency=price_data.currency,
            amount=price_data.amount,
            active=price_data.active,
            recurring_interval=price_data.recurring_interval,
            recurring_interval_count=price_data.recurring_interval_count,
            trial_period_days=price_data.trial_period_days,
            db_sess=db_sess,
        )

        product.price_id = price.id

        return self._create_product_response(product)

    async def get_product_by_id(
        self, product_id: UUID, db_sess: AsyncSession
    ) -> ProductResponse:
        product = await db_sess.get(Product, product_id)
        if product is None:
            raise ProductNotFoundException(product_id)
        return self._create_product_response(product)

    async def get_product_by_merchant(
        self, product_id: UUID, merchant_id: UUID, db_sess: AsyncSession
    ) -> ProductResponse:
        product = await self._get_product(product_id, merchant_id, db_sess)
        return self._create_product_response(product)

    async def get_products_by_merchant(
        self, merchant_id: UUID, page: int, limit: int, db_sess: AsyncSession
    ) -> PaginatedResponse:
        offset = (page - 1) * limit
        result = await db_sess.execute(
            select(Product)
            .where(Product.workspace_id == merchant_id)
            .offset(offset)
            .limit(limit + 1)
        )
        rows = list(result.scalars().all())
        has_next = len(rows) > limit
        data = [self._create_product_response(p) for p in rows[:limit]]
        return PaginatedResponse(
            page=page,
            size=len(data),
            has_next=has_next,
            data=data,
        )

    async def update_product(
        self,
        product_id: UUID,
        merchant_id: UUID,
        name: str | None = None,
        description: str | None = None,
        *,
        db_sess: AsyncSession,
    ) -> ProductResponse:
        product = await self._get_product(product_id, merchant_id, db_sess)

        if name is not None:
            product.name = name
        if description is not None:
            product.description = description

        return self._create_product_response(product)

    async def delete_product(
        self, product_id: UUID, merchant_id: UUID, db_sess: AsyncSession
    ) -> None:
        product = await db_sess.scalar(
            select(Product).where(
                Product.id == product_id, Product.workspace_id == merchant_id
            )
        )
        if product is None:
            raise ProductNotFoundException(product_id)
        await db_sess.delete(product)

    async def _get_product(
        self, product_id: UUID, merchant_id: UUID, db_sess: AsyncSession
    ):
        price = await db_sess.scalar(
            select(Product).where(
                Product.id == product_id, Product.workspace_id == merchant_id
            )
        )
        if price is None:
            raise ProductNotFoundException(product_id)
        return price

    def _create_product_response(self, product: Product) -> ProductResponse:
        return ProductResponse(
            id=product.id,
            workspace_id=product.workspace_id,
            name=product.name,
            description=product.description,
            wallet_id=product.wallet_id,
            price_id=product.price_id,
            group_type=product.fulfilment_type,
            external_url=product.external_url,
            group_id=product.group_id,
            roles=product.roles,
            fulfilment_type=product.fulfilment_type,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )
