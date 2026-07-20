from sqlalchemy.ext.asyncio import AsyncSession

from chrima.user.schema import UserDto, UserProfile, WorkspaceMeta
from chrima.workspace import WorkspaceService


async def build_user_profile(
    user: UserDto,
    workspace_service: WorkspaceService,
    db_sess: AsyncSession,
) -> UserProfile:
    """Convert a UserDto into a UserProfile by fetching the user's workspaces."""
    page = await workspace_service.get_by_user(
        user.id, page=1, limit=100, db_sess=db_sess
    )
    return UserProfile(
        **user.model_dump(),
        workspaces=[WorkspaceMeta(id=w.id, name=w.name) for w in page.data],
    )
