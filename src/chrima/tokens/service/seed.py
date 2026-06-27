from sqlalchemy.ext.asyncio import AsyncSession

from .service import TokenService
from ..enums import TokenChain, TokenStandard
from ..schema import TokenResponse

TOKEN_ADDRESSES: dict[str, dict[str, str]] = {
    "ETH": {
        "mainnet": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "sepolia": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
    },
    "USDT": {
        "mainnet": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "sepolia": "0xaA8E23Fb1079EA71e0a56F48a2aA51851D843BE0",
    },
    "USDC": {
        "mainnet": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "sepolia": "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
    },
}


class TokenSeeder:

    def __init__(self, mainnet: bool = False):
        self._service = TokenService()
        self._network = "mainnet" if mainnet else "sepolia"

    async def run(self, db_sess: AsyncSession) -> list[TokenResponse]:
        entries = [
            ("ETH", TokenStandard.ERC_20, TokenChain.ETH),
            ("USDT", TokenStandard.ERC_20, TokenChain.ETH),
            ("USDC", TokenStandard.ERC_20, TokenChain.ETH),
        ]
        tokens = []
        for name, standard, chain in entries:
            print(f"  Seeding token {name} ...")
            token = await self._service.create_token(
                name, standard, chain, TOKEN_ADDRESSES[name][self._network], db_sess
            )
            tokens.append(token)
        return tokens
