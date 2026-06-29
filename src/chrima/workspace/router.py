from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.deps import depends_db_sess, depends_jwt, depends_object
from chrima.api.schema import PaginatedResponse
from chrima.jwt.schema import JWTPayload
from .schema import (
    CreateWorkspaceRequest,
    WorkspaceResponse,
    UpdateWorkspaceRequest,
)
from .service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("/", status_code=201, response_model=WorkspaceResponse)
async def create_workspace(
    body: CreateWorkspaceRequest,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    workspace_service: WorkspaceService = Depends(depends_object(WorkspaceService)),
):
    return await workspace_service.create_workspace(
        user_id=jwt.sub,
        name=body.name,
        platform=body.platform,
        external_id=body.external_id,
        notification_channel_id=body.notification_channel_id,
        db_sess=db_sess,
    )


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    workspace_service: WorkspaceService = Depends(depends_object(WorkspaceService)),
):
    return await workspace_service.get_workspace_by_user(
        workspace_id, jwt.sub, db_sess
    )


@router.get("/", response_model=PaginatedResponse[WorkspaceResponse])
async def list_workspaces(
    page: int = Query(1, ge=1),
    limit: int = Query(1, ge=1, le=100),
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    workspace_service: WorkspaceService = Depends(depends_object(WorkspaceService)),
):
    return await workspace_service.get_workspaces_by_user(jwt.sub, page, limit, db_sess)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: UUID,
    request: UpdateWorkspaceRequest,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    workspace_service: WorkspaceService = Depends(depends_object(WorkspaceService)),
):
    return await workspace_service.update_workspace(
        workspace_id,
        user_id=jwt.sub,
        name=request.name,
        notification_channel_id=request.notification_channel_id,
        db_sess=db_sess,
    )


@router.delete("/{workspace_id}", status_code=204)
async def delete_workspace(
    workspace_id: UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    workspace_service: WorkspaceService = Depends(depends_object(WorkspaceService)),
):
    await workspace_service.delete_workspace(workspace_id, jwt.sub, db_sess)
