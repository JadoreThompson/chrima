from uuid import UUID

import discord
from discord.ext import commands

from chrima.notification.template import DiscordNotificationTemplateEngine
from chrima.price import PriceService
from chrima.price.schema import PriceResponse
from chrima.product import ProductService
from chrima.subscription import SubscriptionBalanceService
from chrima.subscription.enums import SubscriptionStatus
from chrima.subscription.exception import SubscriptionBalanceNotFoundException
from chrima.workspace import WorkspaceService
from core.db import get_db_session

BOT: commands.Bot = None
WORKSPACE_SERVICE: WorkspaceService = None
PRODUCT_SERVICE: ProductService = None
PRICE_SERVICE: PriceService = None
SUBSCRIPTION_SERVICE: SubscriptionBalanceService = None
TEMPLATE_ENGINE: DiscordNotificationTemplateEngine = None


async def products(ctx: discord.Interaction):
    global WORKSPACE_SERVICE
    global PRODUCT_SERVICE
    global PRICE_SERVICE
    global TEMPLATE_ENGINE

    async with get_db_session() as db_sess:
        workspace = await WORKSPACE_SERVICE.get_by_external_id(
            str(ctx.guild_id), db_sess
        )
        product_page = await PRODUCT_SERVICE.list_by_workspace(
            workspace.id, page=1, limit=50, db_sess=db_sess
        )

        products_with_prices: list[tuple[UUID, PriceResponse]] = []
        for product in product_page.data:
            price_page = await PRICE_SERVICE.list_by_product(
                product.id, page=1, limit=50, db_sess=db_sess
            )
            products_with_prices.append((product, price_page.data))

    embed = TEMPLATE_ENGINE.render_product_list(products_with_prices)
    await ctx.response.send_message(embed=embed, ephemeral=True)


async def cancel(ctx: discord.Interaction, product: str):
    global SUBSCRIPTION_SERVICE
    global TEMPLATE_ENGINE

    cancelled = []
    async with get_db_session() as db_sess:
        try:
            sub = await SUBSCRIPTION_SERVICE.get(
                external_id=str(ctx.guild_id),
                platform_user_id=str(ctx.user.id),
                product_id=product,
                db_sess=db_sess,
            )
            if sub.status != SubscriptionStatus.ACTIVE:
                cancelled = []
            else:
                cancelled = [await SUBSCRIPTION_SERVICE.cancel(sub.id, db_sess)]
            await db_sess.commit()
        except SubscriptionBalanceNotFoundException:
            cancelled = []

    embed = TEMPLATE_ENGINE.render_cancel_result(
        cancelled, ctx.user.id, product_id=product
    )
    await ctx.response.send_message(embed=embed, ephemeral=True)


def DiscordBot(
    *,
    workspace_service: WorkspaceService,
    product_service: ProductService,
    price_service: PriceService,
    subscription_service: SubscriptionBalanceService,
    template_engine: DiscordNotificationTemplateEngine,
) -> commands.Bot:
    global WORKSPACE_SERVICE
    global PRODUCT_SERVICE
    global PRICE_SERVICE
    global SUBSCRIPTION_SERVICE
    global TEMPLATE_ENGINE
    global BOT

    WORKSPACE_SERVICE = workspace_service
    PRODUCT_SERVICE = product_service
    PRICE_SERVICE = price_service
    SUBSCRIPTION_SERVICE = subscription_service
    TEMPLATE_ENGINE = template_engine

    intents = discord.Intents.default()
    intents.message_content = True

    BOT = commands.Bot(command_prefix="/", intents=intents)

    BOT.tree.command(name="products", description="List all products in this server")(
        products
    )
    BOT.tree.command(name="cancel", description="Cancel a subscription by product ID")(
        cancel
    )

    @BOT.event
    async def on_ready():
        await BOT.tree.sync()
        print(f"Synced commands as {BOT.user}")

    return BOT
