from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base, uuid_pk, datetime_column
from util import get_datetime


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = uuid_pk()
    username: Mapped[str] = mapped_column(sa.String, nullable=False)
    email: Mapped[str] = mapped_column(sa.String, nullable=False)
    password: Mapped[str] = mapped_column(sa.String, nullable=False)
    jwt_token: Mapped[str] = mapped_column(sa.String, nullable=True)
    created_at: Mapped[datetime] = datetime_column()
    updated_at: Mapped[datetime] = datetime_column(onupdate=get_datetime)

    __table_args__ = (
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
