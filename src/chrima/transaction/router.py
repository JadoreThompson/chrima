from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.deps import depends_db_sess, depends_object
from chrima.api.schema import PaginatedResponse
from .schema import TransactionResponse
from .service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    db_sess: AsyncSession = Depends(depends_db_sess),
    transaction_service: TransactionService = Depends(
        depends_object(TransactionService)
    ),
):
    return await transaction_service.get_transaction(transaction_id, db_sess)


@router.get("/", response_model=PaginatedResponse[TransactionResponse])
async def list_transactions(
    sender: str | None = Query(None),
    product_id: UUID | None = Query(None),
    price_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(1, ge=1, le=100),
    db_sess: AsyncSession = Depends(depends_db_sess),
    transaction_service: TransactionService = Depends(
        depends_object(TransactionService)
    ),
):
    if sender:
        return await transaction_service.get_transactions_by_sender(
            sender, page, limit, db_sess
        )
    if product_id:
        return await transaction_service.get_transactions_by_product(
            product_id, page, limit, db_sess
        )
    if price_id:
        return await transaction_service.get_transactions_by_price(
            price_id, page, limit, db_sess
        )
    return await transaction_service.get_transactions_by_sender(
        "", page, limit, db_sess
    )
