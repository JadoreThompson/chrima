# Docker

Test containers

```bash
docker compose -p chrima-test -f docker-compose.infra.yaml --env-file .env.test up -d
```

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

## Discord

Bot Permissions:

- manage roles
- kick memebers (dev)
- send messages

Note:
The bot's role must be above all other roles which it'll have the power to grant

OAuth:

- subscriber roles: identify, guilds.join
- workspace owner roles: identify, guilds
