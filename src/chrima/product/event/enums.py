from enum import Enum


class ProductEventType(str, Enum):
    WALLET_UPDATED = "product.wallet_updated"
