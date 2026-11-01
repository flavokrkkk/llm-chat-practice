from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.dependencies.dependencies import get_auth_service
from app.core.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.core.schemas.user import UserSchema
from app.core.services.auth_service import AuthService
from app.utils.cookie import REFRESH_TOKEN_COOKIE_KEY, REFRESH_TOKEN_COOKIE_PATH

router = APIRouter()


@router.post("/register", status_code=201)
async def register(
    payload: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserSchema:
    return await auth_service.register(
        password=payload.password, email=payload.email, full_name=payload.full_name
    )


@router.post("/login")
async def login(
    payload: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    response: Response,
) -> TokenResponse:
    login_result = await auth_service.login(
        email=payload.email, password=payload.password
    )

    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_KEY,
        value=login_result.refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        expires=login_result.refresh_expires_at,
        path=REFRESH_TOKEN_COOKIE_PATH,
    )

    response.headers["Cache-Control"] = "no-store"

    return TokenResponse(access_token=login_result.access_token)
