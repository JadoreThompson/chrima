from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.deps import depends_db_sess, depends_object
from chrima.api.schema import PaginatedResponse
from .schema import TokenResponse
from .service import TokenService

router = APIRouter(prefix="/tokens", tags=["tokens"])


@router.get("/{token_id}", response_model=TokenResponse)
async def get_token(
    token_id: UUID,
    db_sess: AsyncSession = Depends(depends_db_sess),
    token_service: TokenService = Depends(depends_object(TokenService)),
):
    return await token_service.get_token(token_id, db_sess)


@router.get("/", response_model=PaginatedResponse[TokenResponse])
async def list_tokens(
    page: int = Query(1, ge=1),
    limit: int = Query(1, ge=1, le=100),
    db_sess: AsyncSession = Depends(depends_db_sess),
    token_service: TokenService = Depends(depends_object(TokenService)),
):
    return await token_service.get_tokens(page, limit, db_sess)
