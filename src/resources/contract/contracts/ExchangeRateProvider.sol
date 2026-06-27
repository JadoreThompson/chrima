// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface AggregatorV3Interface {
    function latestRoundData()
        external
        view
        returns (uint80 roundId, int256 answer, uint256 startedAt, uint256 updatedAt, uint80 answeredInRound);
}

contract ExchangeRateProvider {
    address public owner;

    mapping(string => mapping(string => address)) public feeds;
    mapping(string => mapping(string => string[])) public routes;

    event FeedSet(string indexed base, string indexed quote, address feed);
    event RouteSet(string indexed base, string indexed quote, string[] path);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function setFeed(string memory base, string memory quote, address feed) external onlyOwner {
        feeds[base][quote] = feed;
        emit FeedSet(base, quote, feed);
    }

    function setRoute(string memory base, string memory quote, string[] memory path) external onlyOwner {
        require(path.length >= 2, "Path too short");
        require(
            keccak256(bytes(path[0])) == keccak256(bytes(base)),
            "Path must start with base"
        );
        require(
            keccak256(bytes(path[path.length - 1])) == keccak256(bytes(quote)),
            "Path must end with quote"
        );
        routes[base][quote] = path;
        emit RouteSet(base, quote, path);
    }

    function _readFeed(address feed) private view returns (uint256, uint256) {
        (, int256 answer, , uint256 updatedAt, ) = AggregatorV3Interface(feed).latestRoundData();
        require(answer > 0, "Invalid feed data");
        return (uint256(answer), updatedAt);
    }

    function _tryInverse(string memory base, string memory quote) private view returns (uint256, uint256) {
        address inverseFeed = feeds[quote][base];
        if (inverseFeed != address(0)) {
            (uint256 price, uint256 updatedAt) = _readFeed(inverseFeed);
            return ((1e36 / price), updatedAt);
        }

        string[] memory inversePath = routes[quote][base];
        if (inversePath.length >= 2) {
            uint256 inverseRate = 1e18;
            uint256 minTime = type(uint256).max;

            for (uint256 i = 0; i < inversePath.length - 1; i++) {
                address hopFeed = feeds[inversePath[i]][inversePath[i + 1]];
                require(hopFeed != address(0), "Hop feed missing");

                (uint256 price, uint256 time) = _readFeed(hopFeed);
                inverseRate = (inverseRate * price) / 1e18;
                if (time < minTime) {
                    minTime = time;
                }
            }

            return ((1e36 / inverseRate), minTime);
        }

        revert("No route or inverse found");
    }

    function getRate(string memory base, string memory quote) external view returns (uint256 rate, uint256 updatedAt) {
        if (keccak256(bytes(base)) == keccak256(bytes(quote))) {
            return (1e18, block.timestamp);
        }

        address directFeed = feeds[base][quote];
        if (directFeed != address(0)) {
            return _readFeed(directFeed);
        }

        string[] memory path = routes[base][quote];
        if (path.length >= 2) {
            uint256 result = 1e18;
            uint256 minTime = type(uint256).max;

            for (uint256 i = 0; i < path.length - 1; i++) {
                address hopFeed = feeds[path[i]][path[i + 1]];
                require(hopFeed != address(0), "Hop feed missing");

                (uint256 price, uint256 time) = _readFeed(hopFeed);
                result = (result * price) / 1e18;
                if (time < minTime) {
                    minTime = time;
                }
            }

            return (result, minTime);
        }

        return _tryInverse(base, quote);
    }
}
