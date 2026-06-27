from uuid import UUID


class TransactionNotFoundException(Exception):
    def __init__(self, transaction_id: UUID):
        super().__init__("Transaction not found")
        self.transaction_id = transaction_id
