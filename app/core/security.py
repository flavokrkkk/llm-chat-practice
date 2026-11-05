import asyncio
import hashlib
import secrets
from datetime import UTC, datetime
from typing import NamedTuple
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from app.infrastructure.config.config import JWTConfig
from app.infrastructure.errors.auth_exceptions import InvalidToken
from app.utils.date import get_expires_at


class GeneratedRefreshToken(NamedTuple):
    raw_token: str
    token_hash: str


class PasswordHasher:
    def __init__(self, max_concurrency: int) -> None:
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._hasher = PasswordHash.recommended()
        self.dummy_hash = self._hasher.hash("dummy-password-for-timing")

    async def hash_password(self, password: str) -> str:
        async with self._semaphore:
            return await asyncio.to_thread(self._hasher.hash, password)

    async def verify_password(self, password: str, hashed_password: str) -> bool:
        async with self._semaphore:
            return await asyncio.to_thread(
                self._hasher.verify, password, hashed_password
            )

    async def verify_and_update_password(
        self, password: str, hashed_password: str
    ) -> tuple[bool, str | None]:
        return await asyncio.to_thread(
            self._hasher.verify_and_update, password, hashed_password
        )


class JWTManager:
    def __init__(self, config: JWTConfig) -> None:
        self._config = config

    @property
    def refresh_token_ttl(self) -> int:
        return self._config.refresh_token_ttl_days

    def create_access_token(self, user_id: UUID) -> str:
        now = datetime.now(UTC)
        expire = get_expires_at(now, minutes=self._config.access_token_ttl_minutes)
        payload = {"exp": expire, "iat": now, "sub": str(user_id)}

        return jwt.encode(
            payload,
            key=self._config.secret.get_secret_value(),
            algorithm=self._config.algorithm,
        )

    def verify_token(self, token: str) -> UUID:
        try:
            payload = jwt.decode(
                token,
                key=self._config.secret.get_secret_value(),
                algorithms=[self._config.algorithm],
                options={"require": ["exp", "iat", "sub"]},
            )

            sub = payload["sub"]

            if not isinstance(sub, str):
                raise InvalidToken

            user_id = UUID(sub)

            return user_id

        except (jwt.InvalidTokenError, ValueError):
            raise InvalidToken from None


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def generate_refresh_token() -> GeneratedRefreshToken:
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_refresh_token(raw_token)

    return GeneratedRefreshToken(raw_token=raw_token, token_hash=token_hash)
