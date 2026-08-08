import click

from chrima.discord import DiscordBot
from chrima.event_bus.publisher import OutboxEventPublisher
from chrima.notification.template import DiscordNotificationTemplateEngine
from chrima.price import PriceService
from chrima.product import ProductService
from chrima.subscription import SubscriptionBalanceService
from chrima.wallet import WalletService
from chrima.workspace import WorkspaceService
from config import DISCORD_BOT_TOKEN


@click.group(name="discord")
def discord():
    pass


@discord.command(name="bot")
def run_discord_bot():
    event_publisher = OutboxEventPublisher()
    workspace_service = WorkspaceService()
    price_service = PriceService(event_publisher=event_publisher)
    product_service = ProductService(event_publisher=event_publisher, wallet_service=WalletService())
    subscription_service = SubscriptionBalanceService(event_publisher=event_publisher)

    bot = DiscordBot(
        workspace_service=workspace_service,
        product_service=product_service,
        price_service=price_service,
        subscription_service=subscription_service,
        template_engine=DiscordNotificationTemplateEngine(),
    )
    bot.run(DISCORD_BOT_TOKEN)
