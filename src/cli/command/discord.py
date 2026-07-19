import click

from chrima.discord.bot import DiscordBot
from chrima.event_bus.publisher.outbox import OutboxEventPublisher
from chrima.notification.template import DiscordNotificationTemplateEngine
from chrima.price import PriceService
from chrima.product import ProductService
from chrima.subscription import SubscriptionBalanceService
from chrima.tokens.service.token import TokenService
from chrima.workspace import WorkspaceService
from config import DISCORD_BOT_TOKEN


@click.group(name="discord")
def discord():
    pass


@discord.command(name="bot")
def run_discord_bot():
    event_publisher = OutboxEventPublisher()
    workspace_service = WorkspaceService()
    token_service = TokenService()
    price_service = PriceService(
        token_service=token_service, event_publisher=event_publisher
    )
    product_service = ProductService(
        price_service=price_service, event_publisher=event_publisher
    )
    subscription_service = SubscriptionBalanceService()

    bot = DiscordBot(
        workspace_service=workspace_service,
        product_service=product_service,
        price_service=price_service,
        subscription_service=subscription_service,
        template_engine=DiscordNotificationTemplateEngine(),
    )
    bot.run(DISCORD_BOT_TOKEN)
