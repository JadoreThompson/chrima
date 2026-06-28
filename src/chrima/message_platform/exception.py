class UserNotInGuildException(Exception):
    def __init__(self, user_id: int, guild_id: int):
        super().__init__(f"User {user_id} is not a member of guild {guild_id}")
        self.user_id = user_id
        self.guild_id = guild_id
