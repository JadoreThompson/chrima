import json
import logging
import os
import sys
from urllib.parse import quote
from dotenv import load_dotenv

SRC_PATH = os.path.dirname(__file__)
PROJECT_PATH = os.path.dirname(SRC_PATH)

PYTEST_RUNNING = os.getenv("PYTEST_VERSION")
load_dotenv(os.path.join(PROJECT_PATH, ".env.test" if PYTEST_RUNNING else ".env"))
del PYTEST_RUNNING

ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
IS_PRODUCTION = ENVIRONMENT == "prod"


# ==========
# Infra
# ==========

# Postgres
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT"))
POSTGRES_USERNAME = os.getenv("POSTGRES_USERNAME")
POSTGRES_PASSWORD = quote(os.getenv("POSTGRES_PASSWORD"))
POSTGRES_DB_NAME = os.getenv("POSTGRES_DB_NAME")
POSTGRES_HOST_CREDS = f"{POSTGRES_HOST}:{POSTGRES_PORT}"
POSTGRES_USER_CREDS = f"{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}"


# Redis
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
REDIS_USERNAME = os.getenv("REDIS_USERNAME")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_DB = int(os.getenv("REDIS_DB", "0"))


# Kafka
KAFKA_HOST = os.getenv("KAFKA_HOST", "localhost")
KAFKA_PORT = int(os.getenv("KAFKA_PORT", "9092"))
KAFKA_BOOTSTRAP_SERVERS = f"{KAFKA_HOST}:{KAFKA_PORT}"

KAKFA_TRANSACTION_EVENTS_TOPIC = os.getenv("KAKFA_TRANSACTION_EVENTS_TOPIC")
KAKFA_PRICE_EVENTS_TOPIC = os.getenv("KAKFA_PRICE_EVENTS_TOPIC")
KAKFA_PRODUCT_EVENTS_TOPIC = os.getenv("KAKFA_PRODUCT_EVENTS_TOPIC")


# ==========
# Server
# ==========

# Server
SCHEME = os.getenv("SCHEME", "http")
DOMAIN = os.getenv("DOMAIN", "localhost:5173")
LOGO_URL = os.getenv(
    "LOGO_URL", "https://pub-11cf41b8c2ec49c2bfbcc1183a3cb4c8.r2.dev/images.jfif"
)


# ==========
# Security
# ==========

# JWT
COOKIE_ALIAS = "chrima-cookie"
JWT_ALGO = os.getenv("JWT_ALGO", "HS256")
JWT_SECRET = os.getenv("JWT_SECRET", "mega-super-duper-uper-secret-key")
JWT_EXPIRY_SECS = int(os.getenv("JWT_EXPIRY_SECS", "100000000"))


# Encryption
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "mega-super-duper-uper-secret-key")
ENCRYPTION_IV_LEN = int(os.getenv("ENCRYPTION_IV_LEN", "12"))


# ==========
# Third Party
# ==========

# Web3 (Ethereum)
RPC_API_KEY = os.getenv("RPC_API_KEY")
RPC_URL_PREFIX = os.getenv("RPC_URL_PREFIX")
RPC_URL = f"{RPC_URL_PREFIX}/{RPC_API_KEY}"
CHRIMA_PAYMENT_CONTRACT_ADDRESS = os.getenv("CHRIMA_PAYMENT_CONTRACT_ADDRESS")
SIGNER_PRIVATE_KEY = os.getenv("SIGNER_PRIVATE_KEY")
fpath = os.path.join(SRC_PATH, "resources", "ChrimaPayment.json")
with open(fpath, "r") as f:
    CHRIMA_PAYMENT_CONTRACT_ABI = json.load(f)


# Discord
DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
DISCORD_CLIENT_ID = os.environ["DISCORD_CLIENT_ID"]
DISCORD_CLIENT_SECRET = os.environ["DISCORD_CLIENT_SECRET"]
DISCORD_REDIRECT_URI = os.getenv(
    "DISCORD_REDIRECT_URI", "http://localhost:8000/auth/discord/oauth/callback"
)


# ==========
# Logging
# ==========

formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(stream_handler)

aiokafka_logger = logging.getLogger("aiokafka")
aiokafka_logger.setLevel(logging.WARNING)

kafka_logger = logging.getLogger("kafka")
kafka_logger.setLevel(logging.WARNING)

discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.WARNING)

discord_client_logger = logging.getLogger("discord.client")
discord_client_logger.setLevel(logging.WARNING)

del root_logger
del aiokafka_logger
del kafka_logger
del discord_logger
del discord_client_logger
