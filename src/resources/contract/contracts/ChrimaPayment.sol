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
    bool public contractDisabled;

    mapping(address => string) public tokenSymbols;
    mapping(string => uint256) public priceIdToAmount;

    event TransactionComplete(
        string product_id,
        string price_id,
        string user_id,
        address indexed sender,
        address indexed recipient,
        address token,
        uint256 tokenAmount
    );

    event TransactionFailed(
        string product_id,
        string price_id,
        string user_id,
        address indexed sender,
        address indexed recipient,
        address token,
        string reason
    );

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier whenEnabled() {
        require(!contractDisabled, "Contract is disabled");
        _;
    }

    constructor(address _exchangeRateProvider) {
        owner = msg.sender;
        exchangeRateProvider = IExchangeRateProvider(_exchangeRateProvider);
    }

    function setExchangeRateProvider(address _exchangeRateProvider) external onlyOwner {
        exchangeRateProvider = IExchangeRateProvider(_exchangeRateProvider);
    }

    function setPrice(string memory price_id, uint256 amount) external onlyOwner {
        require(amount > 0, "Amount must be greater than zero");
        priceIdToAmount[price_id] = amount;
    }

    function toggleContractDisabled() external onlyOwner {
        contractDisabled = !contractDisabled;
    }

    function processTransaction(
        address token,
        address recipient,
        string memory product_id,
        string memory price_id,
        string memory user_id
    ) external payable whenEnabled {
        require(recipient != address(0), "Invalid recipient");

        string memory symbol = tokenSymbols[token];
        require(bytes(symbol).length > 0, "Token symbol not set");

        uint256 currencyAmount = priceIdToAmount[price_id];
        require(currencyAmount > 0, "Price not set");

        string memory currency = "usd";
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
            user_id, 
            msg.sender, 
            recipient, 
            token, 
            tokenAmount
        );
    }

    receive() external payable {}
}
