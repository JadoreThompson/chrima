import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base, uuid_pk
from .enums import TokenStandard, TokenChain


class Token(Base):
    __tablename__ = "tokens"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(sa.String, nullable=False)
    standard: Mapped[TokenStandard] = mapped_column(sa.String, nullable=False)
    chain: Mapped[TokenChain] = mapped_column(sa.String, nullable=False)
    address: Mapped[str] = mapped_column(sa.String, nullable=False)
