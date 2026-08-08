from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.deps import depends_db_sess, depends_jwt, depends_object
from chrima.jwt.schema import JWTPayload
from chrima.product import ProductService
from chrima.workspace import WorkspaceService
from .schema import SubscriptionBalanceResponse
from .service.subscription import SubscriptionBalanceService

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post(
    "/{subscription_balance_id}/cancel",
    response_model=SubscriptionBalanceResponse,
)
async def cancel_subscription(
    subscription_balance_id: UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    subscription_service: SubscriptionBalanceService = Depends(
        depends_object(SubscriptionBalanceService)
    ),
    product_service: ProductService = Depends(depends_object(ProductService)),
    workspace_service: WorkspaceService = Depends(depends_object(WorkspaceService)),
):
    sub = await subscription_service.get_by_id(subscription_balance_id, db_sess)
    product = await product_service.get_by_id(sub.product_id, db_sess)
    _ = await workspace_service.get(product.workspace_id, jwt.sub, db_sess)
    sub = await subscription_service.cancel(subscription_balance_id, db_sess=db_sess)
    await db_sess.commit()
    return sub
