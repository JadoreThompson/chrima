from core.schema import CustomBaseModel


class RegisterRequest(CustomBaseModel):
    username: str
    email: str
    password: str


class LoginRequest(CustomBaseModel):
    email: str
    password: str
