from datetime import UTC, datetime
from typing import NamedTuple
from uuid import uuid4

from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories.refresh_token_repository import RefreshTokenRepository
from app.core.repositories.user_repository import UserRepository
from app.core.schemas.user import UserSchema
from app.core.security import (
    JWTManager,
    PasswordHasher,
    generate_refresh_token,
    hash_refresh_token,
)
from app.infrastructure.errors.auth_exceptions import (
    AccountDisabledError,
    InvalidCredentialsError,
    InvalidToken,
)
from app.infrastructure.errors.exceptions import ConflictError
from app.utils.date import get_expires_at


class LoginResult(NamedTuple):
    refresh_token: str
    access_token: str
    refresh_expires_at: datetime


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        jwt_manager: JWTManager,
        password_hasher: PasswordHasher,
    ) -> None:
        self.session = session
        self.jwt_manager = jwt_manager
        self.password_hasher = password_hasher
        self.user_repository = UserRepository(session)
        self.refresh_token_repository = RefreshTokenRepository(session)

    async def register(
        self, full_name: str, password: SecretStr, email: str
    ) -> UserSchema:
        password_hash = await self.password_hasher.hash_password(
            password.get_secret_value()
        )

        async with self.session.begin():
            user = await self.user_repository.create_user(
                email=email,
                full_name=full_name,
                password_hash=password_hash,
            )

            if user is None:
                raise ConflictError("Email already registered")

            return user

    async def login(self, email: str, password: SecretStr) -> LoginResult:
        async with self.session.begin():
            credentials = await self.user_repository.find_credentials_by_email(email)

        hash_to_check = (
            credentials.password_hash
            if credentials
            else self.password_hasher.dummy_hash
        )

        password_ok = await self.password_hasher.verify_password(
            password.get_secret_value(), hash_to_check
        )

        if credentials is None or not password_ok:
            raise InvalidCredentialsError()

        if not credentials.is_active:
            raise AccountDisabledError()

        refresh_token = generate_refresh_token()
        expires_at = get_expires_at(
            datetime.now(UTC), days=self.jwt_manager.refresh_token_ttl
        )

        access_token = self.jwt_manager.create_access_token(user_id=credentials.id)

        async with self.session.begin():
            await self.refresh_token_repository.create_refresh_token(
                user_id=credentials.id,
                token_hash=refresh_token.token_hash,
                family_id=uuid4(),
                expires_at=expires_at,
            )

        return LoginResult(
            refresh_token=refresh_token.raw_token,
            access_token=access_token,
            refresh_expires_at=expires_at,
        )

    async def refresh(self, refresh_token: str) -> LoginResult:
        token_hash = hash_refresh_token(refresh_token)

        result: LoginResult | None = None
        account_disabled_or_invalid_user = False

        async with self.session.begin():
            revoked = await self.refresh_token_repository.revoke_active_by_hash(
                token_hash=token_hash
            )

            if revoked is None:
                existing = await self.refresh_token_repository.find_token_by_hash(
                    token_hash=token_hash
                )

                if existing is not None and existing.revoked_at is not None:
                    await self.refresh_token_repository.revoke_family(
                        existing.family_id
                    )
            else:
                user = await self.user_repository.find_user_by_id(
                    user_id=revoked.user_id
                )

                if user is None or not user.is_active:
                    account_disabled_or_invalid_user = True
                else:
                    expires_at = get_expires_at(
                        datetime.now(UTC), days=self.jwt_manager.refresh_token_ttl
                    )

                    new_refresh_token = generate_refresh_token()

                    new_refresh_token_id = (
                        await self.refresh_token_repository.create_refresh_token(
                            user_id=user.id,
                            family_id=revoked.family_id,
                            token_hash=new_refresh_token.token_hash,
                            expires_at=expires_at,
                        )
                    )

                    await self.refresh_token_repository.set_replaced_by(
                        old_token_id=revoked.id, new_token_id=new_refresh_token_id
                    )

                    new_access_token = self.jwt_manager.create_access_token(
                        user_id=user.id
                    )

                    result = LoginResult(
                        refresh_token=new_refresh_token.raw_token,
                        access_token=new_access_token,
                        refresh_expires_at=expires_at,
                    )

        if account_disabled_or_invalid_user:
            raise AccountDisabledError()

        if result is None:
            raise InvalidToken()

        return result

    async def logout(self, refresh_token: str) -> None:
        token_hash = hash_refresh_token(refresh_token)
        async with self.session.begin():
            existing = await self.refresh_token_repository.find_token_by_hash(
                token_hash=token_hash
            )

            if existing is not None:
                await self.refresh_token_repository.revoke_family(existing.family_id)

        return None
