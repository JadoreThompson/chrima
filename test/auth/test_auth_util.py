from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from chrima.auth.util import build_user_profile
from chrima.user.schema import UserDto, UserProfile, WorkspaceMeta
from chrima.workspace import WorkspaceService


@pytest.fixture
def sample_user_dto():
    return UserDto(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 6, 1, 12, 0, 0),
    )


@pytest.fixture
def mock_workspace_service():
    svc = MagicMock(spec=WorkspaceService)
    svc.get_by_user = AsyncMock()
    return svc


@pytest.fixture
def db_sess():
    return AsyncMock()


@pytest.mark.asyncio(loop_scope="session")
class TestBuildUserProfile:
    async def test_builds_profile_with_workspaces(
        self, sample_user_dto, mock_workspace_service, db_sess
    ):
        """Builds a UserProfile including workspaces returned by the service."""
        ws1 = MagicMock()
        ws1.id = uuid4()
        ws1.name = "Workspace One"
        ws2 = MagicMock()
        ws2.id = uuid4()
        ws2.name = "Workspace Two"

        mock_page = MagicMock()
        mock_page.data = [ws1, ws2]
        mock_workspace_service.get_by_user.return_value = mock_page

        result = await build_user_profile(
            sample_user_dto, mock_workspace_service, db_sess
        )

        assert isinstance(result, UserProfile)
        assert result.id == sample_user_dto.id
        assert result.username == sample_user_dto.username
        assert result.email == sample_user_dto.email
        assert result.created_at == sample_user_dto.created_at
        assert result.updated_at == sample_user_dto.updated_at
        assert len(result.workspaces) == 2
        assert result.workspaces[0] == WorkspaceMeta(id=ws1.id, name=ws1.name)
        assert result.workspaces[1] == WorkspaceMeta(id=ws2.id, name=ws2.name)

        mock_workspace_service.get_by_user.assert_awaited_once_with(
            sample_user_dto.id, page=1, limit=100, db_sess=db_sess
        )

    async def test_builds_profile_with_empty_workspaces(
        self, sample_user_dto, mock_workspace_service, db_sess
    ):
        """Builds a UserProfile with an empty workspaces list when the user has none."""
        mock_page = MagicMock()
        mock_page.data = []
        mock_workspace_service.get_by_user.return_value = mock_page

        result = await build_user_profile(
            sample_user_dto, mock_workspace_service, db_sess
        )

        assert isinstance(result, UserProfile)
        assert result.workspaces == []

    async def test_bubbles_up_workspace_service_error(
        self, sample_user_dto, mock_workspace_service, db_sess
    ):
        """Propagates any exception raised by WorkspaceService.get_by_user."""
        mock_workspace_service.get_by_user.side_effect = RuntimeError("db down")

        with pytest.raises(RuntimeError, match="db down"):
            await build_user_profile(
                sample_user_dto, mock_workspace_service, db_sess
            )
