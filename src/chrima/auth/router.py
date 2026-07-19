from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.deps import depends_db_sess, depends_jwt, depends_object
from chrima.auth import AuthService
from chrima.auth.schema import LoginRequest, RegisterRequest, SelectWorkspaceRequest
from chrima.discord.service.discord import DiscordService
from chrima.jwt import JWTService
from chrima.jwt.schema import JWTPayload
from chrima.user import UserService
from chrima.workspace import WorkspaceService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(
    body: RegisterRequest,
    db_sess: AsyncSession = Depends(depends_db_sess),
    auth_service: AuthService = Depends(depends_object(AuthService)),
    user_service: UserService = Depends(depends_object(UserService)),
    jwt_service: JWTService = Depends(depends_object(JWTService)),
):
    user = await auth_service.register_user(body, db_sess)

    rsp = Response(status_code=204)
    jwt_token = jwt_service.set_cookie(rsp, sub=user.id, em=user.email)

    await user_service.set_jwt_token(user.id, jwt_token, db_sess)

    await db_sess.commit()

    return rsp


@router.post("/login")
async def login(
    request: LoginRequest,
    db_sess: AsyncSession = Depends(depends_db_sess),
    auth_service: AuthService = Depends(depends_object(AuthService)),
    jwt_service: JWTService = Depends(depends_object(JWTService)),
    user_service: UserService = Depends(depends_object(UserService)),
):
    user = await auth_service.verify_credentials(request, db_sess)

    rsp = Response(status_code=204)
    jwt_token = jwt_service.set_cookie(rsp, sub=user.id, em=user.email)
    await user_service.set_jwt_token(user.id, jwt_token, db_sess)

    await db_sess.commit()

    return rsp


@router.post("/select-workspace")
async def select_workspace(
    body: SelectWorkspaceRequest,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    jwt_service: JWTService = Depends(depends_object(JWTService)),
    user_service: UserService = Depends(depends_object(UserService)),
    workspace_service: WorkspaceService = Depends(depends_object(WorkspaceService)),
):
    _ = await workspace_service.get_by_id(body.workspace_id, db_sess)

    rsp = Response(status_code=204)
    jwt_token = jwt_service.set_cookie(
        rsp, sub=jwt.sub, em=jwt.em, workspace_id=body.workspace_id
    )
    await user_service.set_jwt_token(jwt.sub, jwt_token, db_sess)

    await db_sess.commit()

    return rsp


@router.post("/logout")
async def logout(
    jwt: JWTPayload = Depends(depends_jwt),
    jwt_service: JWTService = Depends(depends_object(JWTService)),
    user_service: UserService = Depends(depends_object(UserService)),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    rsp = JSONResponse(status_code=200, content={"message": "Logged out"})
    jwt_service.remove_cookie(rsp)
    await user_service.set_jwt_token(jwt.sub, None, db_sess)

    await db_sess.commit()

    return rsp


@router.get("/discord/oauth/callback")
async def discord_oauth_callback(
    code: str,
    jwt: JWTPayload = Depends(depends_jwt),
    discord_oauth_service: DiscordService = Depends(depends_object(DiscordService)),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    print("Disocrd OAuth code:", code)
    oauth_payload = await discord_oauth_service.handle_callback(
        user_id=jwt.sub, code=code, db_sess=db_sess
    )
    print("Discord OAuth payload:", oauth_payload)
    await db_sess.commit()
