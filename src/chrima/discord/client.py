import discord


def DiscordClient() -> discord.Client:
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    return client
