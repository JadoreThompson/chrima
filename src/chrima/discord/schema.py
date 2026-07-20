from pydantic import BaseModel


class DiscordUserResponse(BaseModel):
    id: str
    username: str
    avatar: str | None = None


class DiscordGuildResponse(BaseModel):
    id: str
    name: str
    avatar: str | None = None


class DiscordChannelResponse(BaseModel):
    id: str
    name: str
