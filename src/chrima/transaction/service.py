from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.schema import PaginatedResponse

from .exception import TransactionNotFoundException
from .model import Transaction
from .schema import TransactionResponse


class TransactionService:

    def __init__(self):
        pass

    async def get_transaction(
        self, transaction_id: UUID, db_sess: AsyncSession
    ) -> TransactionResponse:
        transaction = await db_sess.get(Transaction, transaction_id)
        if transaction is None:
            raise TransactionNotFoundException(transaction_id)
        return self._create_transaction_response(transaction)

    async def get_transactions_by_sender(
        self, sender: str, page: int, limit: int, db_sess: AsyncSession
    ) -> PaginatedResponse:
        offset = (page - 1) * limit
        result = await db_sess.execute(
            select(Transaction)
            .where(Transaction.sender == sender)
            .order_by(Transaction.timestamp.desc())
            .offset(offset)
            .limit(limit + 1)
        )
        rows = list(result.scalars().all())
        has_next = len(rows) > limit
        data = [self._create_transaction_response(t) for t in rows[:limit]]
        return PaginatedResponse(
            page=page,
            size=len(data),
            has_next=has_next,
            data=data,
        )

    async def get_transactions_by_product(
        self, product_id: UUID, page: int, limit: int, db_sess: AsyncSession
    ) -> PaginatedResponse:
        offset = (page - 1) * limit
        result = await db_sess.execute(
            select(Transaction)
            .where(Transaction.product_id == product_id)
            .order_by(Transaction.timestamp.desc())
            .offset(offset)
            .limit(limit + 1)
        )
        rows = list(result.scalars().all())
        has_next = len(rows) > limit
        data = [self._create_transaction_response(t) for t in rows[:limit]]
        return PaginatedResponse(
            page=page,
            size=len(data),
            has_next=has_next,
            data=data,
        )

    async def get_transactions_by_price(
        self, price_id: UUID, page: int, limit: int, db_sess: AsyncSession
    ) -> PaginatedResponse:
        offset = (page - 1) * limit
        result = await db_sess.execute(
            select(Transaction)
            .where(Transaction.price_id == price_id)
            .order_by(Transaction.timestamp.desc())
            .offset(offset)
            .limit(limit + 1)
        )
        rows = list(result.scalars().all())
        has_next = len(rows) > limit
        data = [self._create_transaction_response(t) for t in rows[:limit]]
        return PaginatedResponse(
            page=page,
            size=len(data),
            has_next=has_next,
            data=data,
        )

    def _create_transaction_response(
        self, transaction: Transaction
    ) -> TransactionResponse:
        return TransactionResponse(
            id=transaction.id,
            product_id=transaction.product_id,
            price_id=transaction.price_id,
            sender=transaction.sender,
            address=transaction.address,
            amount=transaction.amount,
            status=transaction.status,
            timestamp=transaction.timestamp,
        )
