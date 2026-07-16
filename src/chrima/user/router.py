from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.deps import depends_db_sess, depends_jwt, depends_object
from chrima.jwt.schema import JWTPayload
from chrima.workspace import WorkspaceService
from .schema import UserProfile, WorkspaceMeta
from .service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
async def me(
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    user_service: UserService = Depends(depends_object(UserService)),
    workspace_service: WorkspaceService = Depends(depends_object(WorkspaceService)),
):
    user = await user_service.get_by_id(jwt.sub, db_sess)
    page = await workspace_service.get_by_user(
        jwt.sub, page=1, limit=100, db_sess=db_sess
    )
    return UserProfile(
        **user.model_dump(),
        workspaces=[WorkspaceMeta(id=w.id, name=w.name) for w in page.data],
    )
