from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response

from app.api.dependencies.dependencies import get_auth_service
from app.core.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.core.schemas.user import UserSchema
from app.core.services.auth_service import AuthService
from app.infrastructure.errors.auth_exceptions import InvalidToken
from app.utils.cookie import (
    REFRESH_TOKEN_COOKIE_KEY,
    delete_refresh_cookie,
    set_refresh_cookie,
)

router = APIRouter()


@router.post("/register", status_code=201)
async def register(
    payload: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserSchema:
    return await auth_service.register(
        password=payload.password, email=payload.email, full_name=payload.full_name
    )


# @router.post("/login", dependencies=[Depends(limit_login)])
@router.post("/login")
async def login(
    payload: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    response: Response,
) -> TokenResponse:
    login_result = await auth_service.login(
        email=payload.email, password=payload.password
    )

    set_refresh_cookie(
        response=response,
        value=login_result.refresh_token,
        expires_at=login_result.refresh_expires_at,
    )

    return TokenResponse(access_token=login_result.access_token)


@router.post("/refresh")
async def refresh_token(
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    refresh_token_cookie: Annotated[
        str | None, Cookie(alias=REFRESH_TOKEN_COOKIE_KEY)
    ] = None,
) -> TokenResponse:
    if refresh_token_cookie is None:
        raise InvalidToken()

    token_result = await auth_service.refresh(refresh_token_cookie)

    set_refresh_cookie(
        response=response,
        value=token_result.refresh_token,
        expires_at=token_result.refresh_expires_at,
    )

    return TokenResponse(access_token=token_result.access_token)


@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    refresh_token_cookie: Annotated[
        str | None, Cookie(alias=REFRESH_TOKEN_COOKIE_KEY)
    ] = None,
) -> None:
    if refresh_token_cookie is None:
        return None

    await auth_service.logout(refresh_token_cookie)

    delete_refresh_cookie(response)
