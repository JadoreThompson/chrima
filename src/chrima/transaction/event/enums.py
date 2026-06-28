from enum import Enum


class TransactionEventType(str, Enum):
    COMPLETED = "transaction.completed"
