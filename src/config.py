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
POSTGRES_HOST = os.environ["POSTGRES_HOST"]
POSTGRES_PORT = int(os.environ["POSTGRES_PORT"])
POSTGRES_USERNAME = os.environ["POSTGRES_USERNAME"]
POSTGRES_PASSWORD = quote(os.environ["POSTGRES_PASSWORD"])
POSTGRES_DB = os.environ["POSTGRES_DB"]
POSTGRES_HOST_CREDS = f"{POSTGRES_HOST}:{POSTGRES_PORT}"
POSTGRES_USER_CREDS = f"{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}"


# Redis
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = int(os.environ["REDIS_PORT"])
REDIS_USERNAME = os.environ["REDIS_USERNAME"]
REDIS_PASSWORD = os.environ["REDIS_PASSWORD"]
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

REDIS_CHECKOUT_SESSION_PREFIX = os.getenv(
    "REDIS_CHECKOUT_SESSION_PREFIX", "checkout_session:"
)


# Kafka
KAFKA_HOST = os.getenv("KAFKA_HOST", "localhost")
KAFKA_PORT = int(os.getenv("KAFKA_PORT", "9092"))
KAFKA_BOOTSTRAP_SERVERS = f"{KAFKA_HOST}:{KAFKA_PORT}"

KAKFA_TRANSACTION_EVENTS_TOPIC = os.environ["KAKFA_TRANSACTION_EVENTS_TOPIC"]
KAKFA_PRICE_EVENTS_TOPIC = os.environ["KAKFA_PRICE_EVENTS_TOPIC"]
KAKFA_PRODUCT_EVENTS_TOPIC = os.environ["KAKFA_PRODUCT_EVENTS_TOPIC"]
KAKFA_SUBSCRIPTION_EVENTS_TOPIC = os.environ["KAKFA_SUBSCRIPTION_EVENTS_TOPIC"]
KAKFA_BILLING_EVENTS_TOPIC = os.getenv("KAKFA_BILLING_EVENTS_TOPIC", "billing-events")


# ==========
# Observability
# ==========

SERVICE_NAME = os.getenv("SERVICE_NAME")

# Loki
LOKI_BASE_URL = os.getenv("LOKI_BASE_URL")
LOKI_TIMEOUT = float(os.getenv("LOKI_TIMEOUT", "2.0"))


# Prometheus
PROMETHEUS_METRICS_PORT = int(os.getenv("PROMETHEUS_METRICS_PORT", "8001"))


# Tempo
TEMPO_BASE_URL = os.getenv("TEMPO_BASE_URL")


# ==========
# Server
# ==========
SCHEME = os.getenv("SHCEME", "http")
DOMAIN = os.getenv("DOMAIN", "localhost:3001")
LOGO_URL = os.getenv(
    "LOGO_URL",
    "https://pub-11cf41b8c2ec49c2bfbcc1183a3cb4c8.r2.dev/images.jfif",
)


# ==========
# Security
# ==========

# JWT
COOKIE_ALIAS = os.getenv("COOKIE_ALIAS", "chrima-cookie")
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
RPC_URL: str = os.environ["RPC_URL"]
CHRIMA_PAYMENT_CONTRACT_ADDRESS = os.environ["CHRIMA_PAYMENT_CONTRACT_ADDRESS"]
SIGNER_PRIVATE_KEY = os.environ["SIGNER_PRIVATE_KEY"]
fpath = os.path.join(SRC_PATH, "resources", "contract", "ChrimaPayment.json")
with open(fpath, "r") as f:
    CHRIMA_PAYMENT_CONTRACT_ABI = json.load(f)


# Discord
DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
DISCORD_CLIENT_ID = os.environ["DISCORD_CLIENT_ID"]
DISCORD_CLIENT_SECRET = os.environ["DISCORD_CLIENT_SECRET"]
DISCORD_REDIRECT_URI = os.environ["DISCORD_REDIRECT_URI"]
DISCORD_API_BASE_URL = os.getenv("DISCORD_API_BASE_URL", "https://discord.com/api/v10")


# Billing
BILLING_PROVIDER = os.getenv("BILLING_PROVIDER", "stripe")
BILLING_SUCCESS_URL = os.getenv(
    "BILLING_SUCCESS_URL", "http://localhost:3001/billing/success"
)
BILLING_CANCEL_URL = os.getenv(
    "BILLING_CANCEL_URL", "http://localhost:3001/billing/cancel"
)

STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_PRO_PRICE_ID = os.getenv("STRIPE_PRO_PRICE_ID")


# ==========
# Logging
# ==========

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.setLevel(logging.getLevelNamesMapping().get(LOG_LEVEL, 20))  # Default: INFO
root_logger.addHandler(stream_handler)

if LOKI_BASE_URL and SERVICE_NAME:
    from core.logging.formatter import JsonLogFormatter
    from core.logging.handler import LokiLogHandler

    print("Configuring loki log handler")
    loki_handler = LokiLogHandler(
        LOKI_BASE_URL,
        labels={"service": SERVICE_NAME, "environment": ENVIRONMENT},
        timeout=LOKI_TIMEOUT,
    )
    loki_handler.setFormatter(JsonLogFormatter())
    root_logger.addHandler(loki_handler)
    del loki_handler
    print("Configured loki log handler")

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
