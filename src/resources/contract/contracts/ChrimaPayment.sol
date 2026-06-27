// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
    function decimals() external view returns (uint8);
}

interface IExchangeRateProvider {
    function getRate(string memory base, string memory quote) external view returns (uint256 rate, uint256 updatedAt);
}

contract ChrimaPayment {
    address public owner;
    IExchangeRateProvider public exchangeRateProvider;

    mapping(address => bool) public supportedTokens;
    mapping(address => string) public tokenSymbols;

    event TransactionComplete(
        string product_id,
        string price_id,
        string group_user_id,
        address indexed sender,
        address indexed recipient,
        address token,
        uint256 tokenAmount
    );

    event TransactionFailed(
        string product_id,
        string price_id,
        string group_user_id,
        address indexed sender,
        address indexed recipient,
        address token,
        string reason
    );

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    constructor(address _exchangeRateProvider) {
        owner = msg.sender;
        exchangeRateProvider = IExchangeRateProvider(_exchangeRateProvider);
    }

    function setExchangeRateProvider(address _exchangeRateProvider) external onlyOwner {
        exchangeRateProvider = IExchangeRateProvider(_exchangeRateProvider);
    }

    function setSupportedToken(address token, string memory symbol, bool supported) external onlyOwner {
        supportedTokens[token] = supported;
        tokenSymbols[token] = symbol;
    }

    function processTransaction(
        address token,
        address recipient,
        string memory product_id,
        string memory price_id,
        string memory group_user_id,
        string memory currency,
        uint256 currencyAmount
    ) external payable {
        require(recipient != address(0), "Invalid recipient");
        require(supportedTokens[token], "Token not supported");

        string memory symbol = tokenSymbols[token];
        require(bytes(symbol).length > 0, "Token symbol not set");

        (uint256 rate, ) = exchangeRateProvider.getRate(currency, symbol);
        require(rate > 0, "Invalid rate");

        uint8 tokenDecimals = 18;
        if (address(token) != address(0)) {
            tokenDecimals = IERC20(token).decimals();
        }

        uint256 tokenAmount = (currencyAmount * rate) / 1e18;

        if (tokenDecimals < 18) {
            tokenAmount = tokenAmount / (10 ** (18 - tokenDecimals));
        } else if (tokenDecimals > 18) {
            tokenAmount = tokenAmount * (10 ** (tokenDecimals - 18));
        }

        if (address(token) == address(0)) {
            require(msg.value == tokenAmount, "Incorrect ETH amount");
        } else {
            IERC20(token).transferFrom(msg.sender, recipient, tokenAmount);
        }

        emit TransactionComplete(
            product_id, 
            price_id, 
            group_user_id, 
            msg.sender, 
            recipient, 
            token, 
            tokenAmount
        );
    }

    receive() external payable {}
}
