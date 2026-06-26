from enum import Enum


class TokenChain(str, Enum):
    ETH = "eth"
    """Ethereum"""


class TokenStandard(str, Enum):
    ERC_20 = "erc-20"
    """Ethereum chain token standard"""
