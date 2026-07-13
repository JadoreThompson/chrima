import logging

from web3 import AsyncWeb3
from web3.contract.async_contract import AsyncContract

from config import (
    CHRIMA_PAYMENT_CONTRACT_ABI,
    CHRIMA_PAYMENT_CONTRACT_ADDRESS,
    RPC_URL,
    SIGNER_PRIVATE_KEY,
)


class PaymentService:
    def __init__(
        self,
        rpc_url: str = RPC_URL,
        contract_address: str = CHRIMA_PAYMENT_CONTRACT_ADDRESS,
        abi: list[dict] = CHRIMA_PAYMENT_CONTRACT_ABI,
        private_key: str = SIGNER_PRIVATE_KEY,
    ):
        self._private_key = private_key
        self._logger = logging.getLogger("payment_client")

        self._w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(rpc_url))
        self._contract: AsyncContract = self._w3.eth.contract(
            address=AsyncWeb3.to_checksum_address(contract_address),
            abi=abi,
        )

    async def set_price(self, price_id: str, amount: float) -> None:
        account = self._w3.eth.account.from_key(self._private_key)
        usd_amount = int(amount)

        tx = await self._contract.functions.setPrice(
            price_id, usd_amount
        ).build_transaction(
            {
                "from": account.address,
                "nonce": await self._w3.eth.get_transaction_count(account.address),
                "gas": 100000,
                "gasPrice": await self._w3.eth.gas_price,
            }
        )

        signed = account.sign_transaction(tx)
        tx_hash = await self._w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = await self._w3.eth.wait_for_transaction_receipt(tx_hash)

        self._logger.info(
            "set_price tx hash=%s price_id=%s amount=%s status=%s",
            tx_hash.hex(),
            price_id,
            amount,
            receipt["status"],
        )
