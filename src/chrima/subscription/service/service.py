from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.price.enums import RecurringInterval
from util import get_datetime
from ..enums import SubscriptionStatus
from ..exception import SubscriptionBalanceNotFoundException
from ..model import SubscriptionBalance
from ..schema import SubscriptionBalanceResponse


class SubscriptionBalanceService:
    def __init__(self):
        pass

    async def get(
        self,
        external_id: str,
        platform_user_id: str,
        product_id: UUID,
        db_sess: AsyncSession,
    ) -> SubscriptionBalanceResponse:
        balance = await db_sess.scalar(
            select(SubscriptionBalance).where(
                SubscriptionBalance.external_id == external_id,
                SubscriptionBalance.platform_user_id == platform_user_id,
                SubscriptionBalance.product_id == product_id,
            )
        )
        if balance is None:
            raise SubscriptionBalanceNotFoundException(
                external_id, platform_user_id, product_id
            )
        return self._create_response(balance)

    async def get_by_id(self, subscription_balance_id: UUID, db_sess: AsyncSession):
        balance = await db_sess.get(SubscriptionBalance, subscription_balance_id)
        return balance

    async def create(
        self,
        external_id: str,
        platform_user_id: str,
        product_id: UUID,
        credit_amount: float,
        status: SubscriptionStatus,
        cycle_start: int | None = None,
        cycle_end: int | None = None,
        last_processed_tx: UUID | None = None,
        *,
        db_sess: AsyncSession,
    ) -> SubscriptionBalanceResponse:
        balance = SubscriptionBalance(
            external_id=external_id,
            platform_user_id=platform_user_id,
            product_id=product_id,
            credit_amount=credit_amount,
            cycle_start=cycle_start,
            cycle_end=cycle_end,
            status=status,
            last_processed_tx=last_processed_tx,
        )
        db_sess.add(balance)
        await db_sess.flush()
        await db_sess.refresh(balance)
        return self._create_response(balance)

    async def increase_balance(
        self,
        external_id: str,
        platform_user_id: str,
        product_id: UUID,
        amount: float,
        transaction_id: UUID,
        *,
        db_sess: AsyncSession,
    ) -> SubscriptionBalanceResponse:
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
        
        if not transaction_id:
            raise ValueError("Transaction ID must be provided")
        
        balance = await db_sess.scalar(
            select(SubscriptionBalance).where(
                SubscriptionBalance.external_id == external_id,
                SubscriptionBalance.platform_user_id == platform_user_id,
                SubscriptionBalance.product_id == product_id,
            )
        )
        if balance is None:
            raise SubscriptionBalanceNotFoundException(
                external_id, platform_user_id, product_id
            )
        balance.credit_amount += amount
        balance.last_processed_tx = transaction_id
        await db_sess.flush()
        await db_sess.refresh(balance)
        return self._create_response(balance)

    async def process_cycle(
        self,
        external_id: str,
        platform_user_id: str,
        product_id: UUID,
        amount: float,
        recurring_interval: RecurringInterval,
        recurring_interval_count: int,
        transaction_id: UUID,
        *,
        db_sess: AsyncSession,
    ) -> SubscriptionBalanceResponse:
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
        
        if not transaction_id:
            raise ValueError("Transaction ID must be provided")

        balance = await db_sess.scalar(
            select(SubscriptionBalance).where(
                SubscriptionBalance.external_id == external_id,
                SubscriptionBalance.platform_user_id == platform_user_id,
                SubscriptionBalance.product_id == product_id,
            )
        )

        if balance is None:
            raise SubscriptionBalanceNotFoundException(
                external_id, platform_user_id, product_id
            )

        balance.credit_amount -= amount
        now = get_datetime()
        balance.cycle_start = int(now.timestamp())

        if recurring_interval and recurring_interval_count:
            if recurring_interval == "day":
                balance.cycle_end = (
                    balance.cycle_start + 86400 * recurring_interval_count
                )
            elif recurring_interval == "month":
                balance.cycle_end = (
                    balance.cycle_start + 2592000 * recurring_interval_count
                )
            else:
                balance.cycle_end = None
        else:
            balance.cycle_end = None

        balance.last_processed_tx = transaction_id
        await db_sess.flush()
        await db_sess.refresh(balance)
        return self._create_response(balance)

    def _create_response(
        self, balance: SubscriptionBalance
    ) -> SubscriptionBalanceResponse:
        return SubscriptionBalanceResponse(
            id=balance.id,
            external_id=balance.external_id,
            platform_user_id=balance.platform_user_id,
            product_id=balance.product_id,
            credit_amount=balance.credit_amount,
            cycle_start=balance.cycle_start,
            cycle_end=balance.cycle_end,
            status=balance.status,
            last_processed_tx=balance.last_processed_tx,
            attempt_count=balance.attempt_count,
            last_notified_at=balance.last_notified_at,
            updated_at=balance.updated_at,
        )
