from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.event_bus.publisher import EventPublisher
from chrima.price.enums import RecurringInterval
from util import get_datetime
from ..enums import SubscriptionStatus
from ..event import SubscriptionCancelledEvent
from ..exception import (
    SubscriptionBalanceAlreadyCancelledException,
    SubscriptionBalanceNotFoundException,
)
from ..model import SubscriptionBalance
from ..schema import SubscriptionBalanceResponse


class SubscriptionBalanceService:
    def __init__(self, *, event_publisher: EventPublisher):
        self._event_publisher = event_publisher

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

    async def get_by_id(
        self, subscription_balance_id: UUID, db_sess: AsyncSession
    ) -> SubscriptionBalanceResponse:
        balance = await db_sess.get(SubscriptionBalance, subscription_balance_id)
        if balance is None:
            raise SubscriptionBalanceNotFoundException(
                balance_id=subscription_balance_id
            )
        return self._create_response(balance)

    async def list_by_user_group(
        self, user_id: int, external_id: int, db_sess: AsyncSession
    ) -> list[SubscriptionBalanceResponse]:
        rows = await db_sess.scalars(
            select(SubscriptionBalance).where(
                SubscriptionBalance.platform_user_id == str(user_id),
                SubscriptionBalance.external_id == str(external_id),
            )
        )

        balances = rows.all()
        return [self._create_response(b) for b in balances]

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

        if recurring_interval == RecurringInterval.DAY:
            balance.cycle_end = (
                balance.cycle_start + 86400 * recurring_interval_count
            )
        elif recurring_interval == RecurringInterval.MONTH:
            balance.cycle_end = (
                balance.cycle_start + 2592000 * recurring_interval_count
            )
        else:
            raise ValueError(f"Unknown recurring interval '{recurring_interval}'")

        balance.last_processed_tx = transaction_id
        await db_sess.flush()
        await db_sess.refresh(balance)
        return self._create_response(balance)

    async def cancel(
        self,
        subscription_balance_id: UUID,
        db_sess: AsyncSession,
    ) -> SubscriptionBalanceResponse:
        balance = await db_sess.get(SubscriptionBalance, subscription_balance_id)
        if balance is None:
            raise SubscriptionBalanceNotFoundException(
                balance_id=subscription_balance_id
            )

        if balance.status == SubscriptionStatus.CANCELLED:
            raise SubscriptionBalanceAlreadyCancelledException(
                balance_id=subscription_balance_id
            )

        balance.status = SubscriptionStatus.CANCELLED
        await db_sess.flush()
        await db_sess.refresh(balance)

        await self._event_publisher.publish(
            SubscriptionCancelledEvent(
                subscription_balance_id=balance.id,
                external_id=balance.external_id,
                platform_user_id=balance.platform_user_id,
                product_id=balance.product_id,
            )
        )

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
