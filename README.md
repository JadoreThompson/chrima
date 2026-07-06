# Smart Contract

Compile

```bash
bunx hardhat compile
```

Deploy

```bash
bunx hardhat run .\scripts\deploy.js --network sepolia
```

Verify

```bash
bunx hardhat verify \
    --network sepolia \
    --constructor-args scripts/arguments.js \
    0x122D688D1690482f30Ab49bbB673266ac31f07Ab \
    --verbose
```
