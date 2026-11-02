from datetime import datetime

from fastapi import Response

REFRESH_TOKEN_COOKIE_KEY = "refresh_token"
REFRESH_TOKEN_COOKIE_PATH = "/api/v1/auth"


def set_refresh_cookie(response: Response, value: str, expires_at: datetime):
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_KEY,
        value=value,
        httponly=True,
        secure=True,
        samesite="strict",
        expires=expires_at,
        path=REFRESH_TOKEN_COOKIE_PATH,
    )

    response.headers["Cache-Control"] = "no-store"


def delete_refresh_cookie(response: Response):
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE_KEY,
        httponly=True,
        secure=True,
        samesite="strict",
        path=REFRESH_TOKEN_COOKIE_PATH,
    )
