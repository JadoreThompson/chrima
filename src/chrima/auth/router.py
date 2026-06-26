from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.deps import depends_db_sess, depends_jwt, depends_object
from chrima.auth import AuthService
from chrima.auth.schema import LoginRequest, RegisterRequest, SelectMerchantRequest
from chrima.jwt import JWTService
from chrima.jwt.schema import JWTPayload
from chrima.user import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(
    body: RegisterRequest,
    db_sess: AsyncSession = Depends(depends_db_sess),
    auth_service: AuthService = Depends(depends_object(AuthService)),
    jwt_service: JWTService = Depends(depends_object(JWTService)),
):
    user = await auth_service.register_user(body, db_sess)
    rsp = Response(status_code=204)
    jwt_token = jwt_service.set_cookie(rsp, sub=user.id, em=user.email)
    user.jwt_token = jwt_token
    await db_sess.commit()
    return rsp


@router.post("/login")
async def login(
    request: LoginRequest,
    db_sess: AsyncSession = Depends(depends_db_sess),
    auth_service: AuthService = Depends(depends_object(AuthService)),
    jwt_service: JWTService = Depends(depends_object(JWTService)),
):
    user = await auth_service.verify_credentials(request, db_sess)

    rsp = Response(status_code=204)
    jwt_token = jwt_service.set_cookie(rsp, sub=user.id, em=user.email)
    user.jwt_token = jwt_token

    await db_sess.commit()

    return rsp


@router.post("/select-merchant")
async def select_merchant(
    body: SelectMerchantRequest,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    jwt_service: JWTService = Depends(depends_object(JWTService)),
    user_service: UserService = Depends(depends_object(UserService)),
):
    user = await user_service.get_user_by_id(jwt.sub, db_sess)
    
    rsp = Response(status_code=204)
    jwt_token = jwt_service.set_cookie(rsp, sub=jwt.sub, em=jwt.em, merchant_id=body.merchant_id)
    user.jwt_token = jwt_token
    await db_sess.commit()

    return rsp


@router.post("/logout")
async def logout(
    jwt: JWTPayload = Depends(depends_jwt),
    jwt_service: JWTService = Depends(depends_object(JWTService)),
    user_service: UserService = Depends(depends_object(UserService)),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    user = await user_service.get_user_by_id(jwt.sub, db_sess)
    rsp = JSONResponse(status_code=200, content={"message": "Logged out"})
    jwt_service.remove_cookie(rsp)
    user.jwt_token = None
    await db_sess.commit()
    return rsp
