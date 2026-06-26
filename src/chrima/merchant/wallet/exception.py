from uuid import UUID


class WalletNotFoundException(Exception):
    def __init__(self, wallet_id: UUID):
        super().__init__("Wallet not found")
        self.wallet_id = wallet_id


class WalletInUseException(Exception):
    def __init__(self, wallet_id: UUID):
        super().__init__("Wallet is in use by one or more products and cannot be deleted")
        self.wallet_id = wallet_id
