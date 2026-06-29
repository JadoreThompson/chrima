from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.schema import PaginatedResponse
from chrima.message_platform.enums import MessagePlatform

from .exception import WorkspaceNotFoundException
from .model import Workspace
from .schema import WorkspaceResponse


class WorkspaceService:

    def __init__(self):
        pass

    async def create_workspace(
        self,
        user_id: UUID,
        name: str,
        platform: MessagePlatform,
        external_id: str,
        notification_channel_id: str,
        db_sess: AsyncSession,
    ) -> WorkspaceResponse:
        workspace = Workspace(
            user_id=user_id,
            name=name,
            platform=platform,
            external_id=external_id,
            notification_channel_id=notification_channel_id,
        )
        db_sess.add(workspace)
        await db_sess.flush()
        await db_sess.refresh(workspace)
        return self._create_response(workspace)

    async def get_workspace(
        self, workspace_id: UUID, db_sess: AsyncSession
    ) -> WorkspaceResponse:
        workspace = await db_sess.get(Workspace, workspace_id)
        if workspace is None:
            raise WorkspaceNotFoundException(workspace_id)
        return self._create_response(workspace)

    async def get_workspace_by_user(
        self, workspace_id: UUID, user_id: UUID, db_sess: AsyncSession
    ) -> WorkspaceResponse:
        workspace = await self._get_workspace(workspace_id, user_id, db_sess)
        return self._create_response(workspace)

    async def get_workspaces_by_user(
        self, user_id: UUID, page: int, limit: int, db_sess: AsyncSession
    ) -> PaginatedResponse:
        offset = (page - 1) * limit

        result = await db_sess.execute(
            select(Workspace)
            .where(Workspace.user_id == user_id)
            .offset(offset)
            .limit(limit + 1)
        )

        rows = list(result.scalars().all())
        has_next = len(rows) > limit
        data = [self._create_response(w) for w in rows[:limit]]

        return PaginatedResponse(
            page=page,
            size=len(data),
            has_next=has_next,
            data=data,
        )

    async def update_workspace(
        self,
        workspace_id: UUID,
        user_id: UUID,
        name: str | None = None,
        notification_channel_id: str | None = None,
        *,
        db_sess: AsyncSession,
    ) -> WorkspaceResponse:
        workspace = await self._get_workspace(workspace_id, user_id, db_sess)

        if name is not None:
            workspace.name = name
        if notification_channel_id is not None:
            workspace.notification_channel_id = notification_channel_id

        return self._create_response(workspace)

    async def delete_workspace(
        self, workspace_id: UUID, user_id: UUID, db_sess: AsyncSession
    ) -> None:
        workspace = await self._get_workspace(workspace_id, user_id, db_sess)
        await db_sess.delete(workspace)

    async def _get_workspace(
        self, workspace_id: UUID, user_id: UUID, db_sess: AsyncSession
    ) -> Workspace:
        workspace = await db_sess.scalar(
            select(Workspace).where(
                Workspace.id == workspace_id, Workspace.user_id == user_id
            )
        )
        if workspace is None:
            raise WorkspaceNotFoundException(workspace_id)

        return workspace

    def _create_response(self, workspace: Workspace) -> WorkspaceResponse:
        return WorkspaceResponse(
            id=workspace.id,
            platform=workspace.platform,
            external_id=workspace.external_id,
            notification_channel_id=workspace.notification_channel_id,
            name=workspace.name,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
        )
