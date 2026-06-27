from enum import Enum


class TransactionStatus(str, Enum):
    COMPLETE = "complete"
    FAILED = "failed"
