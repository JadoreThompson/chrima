from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.schema import PaginatedResponse

from .exception import TokenNotFoundException
from .model import Token
from .schema import TokenResponse


class TokenService:

    def __init__(self):
        pass

    async def create_token(
        self, name: str, standard: str, chain: str, db_sess: AsyncSession
    ) -> TokenResponse:
        token = Token(name=name, standard=standard, chain=chain)
        db_sess.add(token)
        await db_sess.flush()
        await db_sess.refresh(token)
        return self._create_token_response(token)

    async def get_token(self, token_id: UUID, db_sess: AsyncSession) -> TokenResponse:
        token = await db_sess.get(Token, token_id)
        if token is None:
            raise TokenNotFoundException(token_id)
        return self._create_token_response(token)

    async def get_tokens(
        self, page: int, limit: int, db_sess: AsyncSession
    ) -> PaginatedResponse:
        offset = (page - 1) * limit
        result = await db_sess.execute(
            select(Token).offset(offset).limit(limit + 1)
        )
        rows = list(result.scalars().all())
        has_next = len(rows) > limit
        data = [self._create_token_response(t) for t in rows[:limit]]
        return PaginatedResponse(
            page=page,
            size=len(data),
            has_next=has_next,
            data=data,
        )

    async def get_tokens_by_ids(
        self, token_ids: list[UUID], db_sess: AsyncSession
    ) -> list[TokenResponse]:
        if not token_ids:
            return []
        result = await db_sess.execute(
            select(Token).where(Token.id.in_(token_ids))
        )
        return [self._create_token_response(t) for t in result.scalars().all()]

    def _create_token_response(self, token: Token) -> TokenResponse:
        return TokenResponse(
            id=token.id,
            name=token.name,
            standard=token.standard,
            chain=token.chain,
        )
