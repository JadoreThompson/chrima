from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from chrima.api.object_registry import ObjectRegistry
from chrima.payment import PaymentService
from chrima.price import PriceService


@pytest.fixture
def mock_payment_service():
    return AsyncMock(spec=PaymentService)


@pytest.fixture
def price_service(token_service, mock_payment_service):
    return PriceService(
        token_service=token_service, payment_service=mock_payment_service
    )
