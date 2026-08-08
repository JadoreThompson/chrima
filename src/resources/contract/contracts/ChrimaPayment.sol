// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
    function decimals() external view returns (uint8);
}

contract ChrimaPayment {
    address public owner;
    address public usdtToken;

    mapping(bytes16 => uint256) public priceIdToAmount;
    mapping(bytes16 => address) public productIdToRecipient;

    event TransactionComplete(
        bytes16 product_id,
        bytes16 price_id,
        string user_id,
        address indexed sender,
        address indexed recipient,
        uint256 amount
    );

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function setUsdtToken(address _usdtToken) external onlyOwner {
        require(_usdtToken != address(0), "Invalid USDT address");
        usdtToken = _usdtToken;
    }

    function setPrice(bytes16 price_id, uint256 amount) external onlyOwner {
        require(amount > 0, "Amount must be greater than zero");
        priceIdToAmount[price_id] = amount;
    }

    function setProductRecipient(bytes16 product_id, address recipient) external onlyOwner {
        require(recipient != address(0), "Invalid recipient");
        productIdToRecipient[product_id] = recipient;
    }

    function processTransaction(
        bytes16 product_id,
        bytes16 price_id,
        string calldata user_id
    ) external {
        require(usdtToken != address(0), "USDT token not set");

        address recipient = productIdToRecipient[product_id];
        require(recipient != address(0), "Recipient not set for product");

        uint256 usdtAmount = priceIdToAmount[price_id];
        require(usdtAmount > 0, "Price not set");

        IERC20 usdtContract = IERC20(usdtToken);

        require(
            usdtContract.transferFrom(msg.sender, recipient, usdtAmount),
            "USDT transfer failed"
        );

        emit TransactionComplete(
            product_id,
            price_id,
            user_id,
            msg.sender,
            recipient,
            usdtAmount
        );
    }
}