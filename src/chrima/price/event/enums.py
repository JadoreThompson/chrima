from enum import Enum


class PriceEventType(str, Enum):
    PRICE_UPDATED = "price.updated"
