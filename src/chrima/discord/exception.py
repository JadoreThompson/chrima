from uuid import UUID


class DiscordUserNotInGuildException(Exception):
    def __init__(self, user_id: int, guild_id: int):
        super().__init__(f"User {user_id} is not a member of guild {guild_id}")
        self.user_id = user_id
        self.guild_id = guild_id


class DiscordUserNotFoundException(Exception):
    def __init__(self, discord_user_id: int | None = None, user_id: UUID | None = None):
        if discord_user_id is None and user_id is None:
            raise ValueError("Either discord_user_id or user_id must be provided")

        super().__init__(
            f"Discord user {f'{discord_user_id} not found' if discord_user_id is not None else 'not found'}"
        )
        self.user_id = user_id
        self.discord_user_id = discord_user_id


class DiscordGuildNotFoundException(Exception):
    def __init__(self, guild_id: str):
        super().__init__(f"Guild {guild_id} not found")
        self.guild_id = guild_id


class DiscordChannelNotFoundException(Exception):
    def __init__(self, channel_id: str):
        super().__init__(f"Channel {channel_id} not found")
        self.channel_id = channel_id
