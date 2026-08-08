from enum import Enum


class TokenChain(str, Enum):
    ETH = "ethereum"
    """Ethereum"""


class TokenStandard(str, Enum):
    ERC_20 = "erc-20"
    """Ethereum chain token standard"""
