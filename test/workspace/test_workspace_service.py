from uuid import uuid4

import pytest

from chrima.workspace.enums import MessagePlatformType
from chrima.workspace.exception import WorkspaceNotFoundException
from chrima.workspace.model import Workspace
from infra.db import get_db_session


@pytest.fixture
def setup_user(user_service, faker):
    async def _setup():
        async with get_db_session() as db_sess:
            user = await user_service.create(
                username=faker.user_name(),
                email=faker.email(),
                password=faker.password(),
                db_sess=db_sess,
            )
            await db_sess.commit()
            return user

    return _setup


@pytest.mark.asyncio(loop_scope="session")
class TestCreate:

    async def test_creates_workspace(
        self, workspace_service, setup_user, create_drop_tables
    ):
        user = await setup_user()
        async with get_db_session() as db_sess:
            ws = await workspace_service.create(
                user_id=user.id,
                name="test-workspace",
                platform=MessagePlatformType.DISCORD,
                external_id="ext_123",
                notification_channel_id="ch_1",
                db_sess=db_sess,
            )

            assert ws.name == "test-workspace"
            assert ws.platform == MessagePlatformType.DISCORD
            assert ws.external_id == "ext_123"
            assert ws.notification_channel_id == "ch_1"

            row = await db_sess.get(Workspace, ws.id)
            assert row is not None

    async def test_nonexistent_user_raises(self, workspace_service, create_drop_tables):
        async with get_db_session() as db_sess:
            with pytest.raises(Exception):
                await workspace_service.create(
                    user_id=uuid4(),
                    name="test",
                    platform=MessagePlatformType.DISCORD,
                    external_id="ext",
                    notification_channel_id="ch",
                    db_sess=db_sess,
                )


@pytest.mark.asyncio(loop_scope="session")
class TestGetById:

    async def test_returns_workspace(
        self, workspace_service, setup_user, create_drop_tables
    ):
        user = await setup_user()
        async with get_db_session() as db_sess:
            created = await workspace_service.create(
                user_id=user.id,
                name="get-by-id",
                platform=MessagePlatformType.DISCORD,
                external_id="ext",
                notification_channel_id="ch",
                db_sess=db_sess,
            )

            fetched = await workspace_service.get_by_id(created.id, db_sess)
            assert fetched.id == created.id
            assert fetched.name == "get-by-id"

    async def test_raises_when_not_found(self, workspace_service, create_drop_tables):
        async with get_db_session() as db_sess:
            with pytest.raises(WorkspaceNotFoundException):
                await workspace_service.get_by_id(uuid4(), db_sess)


@pytest.mark.asyncio(loop_scope="session")
class TestGet:

    async def test_returns_workspace(
        self, workspace_service, setup_user, create_drop_tables
    ):
        user = await setup_user()
        async with get_db_session() as db_sess:
            created = await workspace_service.create(
                user_id=user.id,
                name="get-ws",
                platform=MessagePlatformType.DISCORD,
                external_id="ext",
                notification_channel_id="ch",
                db_sess=db_sess,
            )

            fetched = await workspace_service.get(created.id, user.id, db_sess)
            assert fetched.id == created.id

    async def test_raises_when_not_found(
        self, workspace_service, setup_user, create_drop_tables
    ):
        user = await setup_user()
        async with get_db_session() as db_sess:
            with pytest.raises(WorkspaceNotFoundException):
                await workspace_service.get(uuid4(), user.id, db_sess)

    async def test_raises_when_wrong_user(
        self, workspace_service, setup_user, create_drop_tables
    ):
        user = await setup_user()
        async with get_db_session() as db_sess:
            created = await workspace_service.create(
                user_id=user.id,
                name="wrong-user",
                platform=MessagePlatformType.DISCORD,
                external_id="ext",
                notification_channel_id="ch",
                db_sess=db_sess,
            )

            with pytest.raises(WorkspaceNotFoundException):
                await workspace_service.get(created.id, uuid4(), db_sess)

            row = await db_sess.get(Workspace, created.id)
            assert row is not None


@pytest.mark.asyncio(loop_scope="session")
class TestGetByUser:

    async def test_returns_workspaces(
        self, workspace_service, setup_user, create_drop_tables
    ):
        user = await setup_user()
        async with get_db_session() as db_sess:
            w1 = await workspace_service.create(
                user_id=user.id,
                name="ws-a",
                platform=MessagePlatformType.DISCORD,
                external_id="ext_a",
                notification_channel_id="ch_a",
                db_sess=db_sess,
            )
            w2 = await workspace_service.create(
                user_id=user.id,
                name="ws-b",
                platform=MessagePlatformType.DISCORD,
                external_id="ext_b",
                notification_channel_id="ch_b",
                db_sess=db_sess,
            )

            result = await workspace_service.get_by_user(
                user.id,
                page=1,
                limit=10,
                db_sess=db_sess,
            )
            assert result.size == 2
            assert {w.id for w in result.data} == {w1.id, w2.id}

    async def test_paginates(self, workspace_service, setup_user, create_drop_tables):
        user = await setup_user()
        async with get_db_session() as db_sess:
            for _ in range(3):
                await workspace_service.create(
                    user_id=user.id,
                    name="ws",
                    platform=MessagePlatformType.DISCORD,
                    external_id="ext",
                    notification_channel_id="ch",
                    db_sess=db_sess,
                )

            result = await workspace_service.get_by_user(
                user.id,
                page=1,
                limit=2,
                db_sess=db_sess,
            )
            assert result.size == 2
            assert result.has_next is True

    async def test_returns_empty_when_no_workspaces(
        self, workspace_service, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            result = await workspace_service.get_by_user(
                uuid4(),
                page=1,
                limit=10,
                db_sess=db_sess,
            )
            assert result.size == 0


@pytest.mark.asyncio(loop_scope="session")
class TestUpdate:

    async def test_updates_name(
        self, workspace_service, setup_user, create_drop_tables
    ):
        user = await setup_user()
        async with get_db_session() as db_sess:
            created = await workspace_service.create(
                user_id=user.id,
                name="original",
                platform=MessagePlatformType.DISCORD,
                external_id="ext",
                notification_channel_id="ch",
                db_sess=db_sess,
            )

            updated = await workspace_service.update(
                created.id,
                user.id,
                name="updated-name",
                db_sess=db_sess,
            )
            assert updated.name == "updated-name"

            row = await db_sess.get(Workspace, created.id)
            assert row.name == "updated-name"

    async def test_updates_channel_id(
        self, workspace_service, setup_user, create_drop_tables
    ):
        user = await setup_user()
        async with get_db_session() as db_sess:
            created = await workspace_service.create(
                user_id=user.id,
                name="ch-test",
                platform=MessagePlatformType.DISCORD,
                external_id="ext",
                notification_channel_id="old_ch",
                db_sess=db_sess,
            )

            updated = await workspace_service.update(
                created.id,
                user.id,
                notification_channel_id="new_ch",
                db_sess=db_sess,
            )
            assert updated.notification_channel_id == "new_ch"

    async def test_raises_when_not_found(
        self, workspace_service, setup_user, create_drop_tables
    ):
        user = await setup_user()
        async with get_db_session() as db_sess:
            with pytest.raises(WorkspaceNotFoundException):
                await workspace_service.update(
                    uuid4(), user.id, name="x", db_sess=db_sess
                )

    async def test_raises_when_wrong_user(
        self, workspace_service, setup_user, create_drop_tables
    ):
        user = await setup_user()
        async with get_db_session() as db_sess:
            created = await workspace_service.create(
                user_id=user.id,
                name="wrong-user-upd",
                platform=MessagePlatformType.DISCORD,
                external_id="ext",
                notification_channel_id="ch",
                db_sess=db_sess,
            )

            with pytest.raises(WorkspaceNotFoundException):
                await workspace_service.update(
                    created.id, uuid4(), name="x", db_sess=db_sess
                )

            row = await db_sess.get(Workspace, created.id)
            assert row.name == "wrong-user-upd"


@pytest.mark.asyncio(loop_scope="session")
class TestDelete:

    async def test_deletes_workspace(
        self, workspace_service, setup_user, create_drop_tables
    ):
        user = await setup_user()
        async with get_db_session() as db_sess:
            created = await workspace_service.create(
                user_id=user.id,
                name="to-delete",
                platform=MessagePlatformType.DISCORD,
                external_id="ext",
                notification_channel_id="ch",
                db_sess=db_sess,
            )

            await workspace_service.delete(created.id, user.id, db_sess)

        async with get_db_session() as db_sess:
            row = await db_sess.get(Workspace, created.id)
            assert row is None

    async def test_raises_when_not_found(
        self, workspace_service, setup_user, create_drop_tables
    ):
        user = await setup_user()
        async with get_db_session() as db_sess:
            with pytest.raises(WorkspaceNotFoundException):
                await workspace_service.delete(uuid4(), user.id, db_sess)

    async def test_raises_when_wrong_user(
        self, workspace_service, setup_user, create_drop_tables
    ):
        user = await setup_user()
        async with get_db_session() as db_sess:
            created = await workspace_service.create(
                user_id=user.id,
                name="wrong-user-del",
                platform=MessagePlatformType.DISCORD,
                external_id="ext",
                notification_channel_id="ch",
                db_sess=db_sess,
            )

            with pytest.raises(WorkspaceNotFoundException):
                await workspace_service.delete(created.id, uuid4(), db_sess)

            row = await db_sess.get(Workspace, created.id)
            assert row is not None
