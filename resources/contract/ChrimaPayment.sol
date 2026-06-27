// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
    function decimals() external view returns (uint8);
}

contract ChrimaPayment {
    address public owner;
    address public feeCollector;

    mapping(address => mapping(string => uint256)) public tokenRates;

    event TransactionComplete(
        string product_id,
        string price_id,
        string group_user_id,
        address indexed sender,
        address indexed recipient,
        address token
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

    constructor(address _feeCollector) {
        owner = msg.sender;
        feeCollector = _feeCollector;
    }

    function setFeeCollector(address _feeCollector) external onlyOwner {
        feeCollector = _feeCollector;
    }

    function setTokenRate(address token, string memory currency, uint256 rate) external onlyOwner {
        tokenRates[token][currency] = rate;
    }

    function convert(
        address token,
        string memory currency,
        uint256 currencyAmount
    ) public view returns (uint256) {
        uint256 rate = tokenRates[token][currency];
        require(rate > 0, "Rate not set");
        uint8 decimals = IERC20(token).decimals();
        return (currencyAmount * rate * (10 ** decimals)) / 1e18;
    }

    function processTransaction(
        address token,
        address recipient,
        string memory product_id,
        string memory price_id,
        string memory group_user_id,
        string memory currency,
        uint256 currencyAmount
    ) external {
        require(recipient != address(0), "Invalid recipient");
        uint256 tokenAmount;

        if (address(token) == address(0)) {
            tokenAmount = msg.value;
        } else {
            tokenAmount = convert(token, currency, currencyAmount);
            IERC20 tokenContract = IERC20(token);
            require(
                tokenContract.transferFrom(msg.sender, recipient, tokenAmount),
                "Transfer failed"
            );
        }

        emit TransactionComplete(product_id, price_id, group_user_id, msg.sender, recipient, token);
    }

    receive() external payable {}
}
