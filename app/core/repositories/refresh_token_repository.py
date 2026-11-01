from datetime import datetime
from typing import NamedTuple
from uuid import UUID

from sqlalchemy import func, insert, select, update

from app.core.schemas.auth import RefreshTokenSchema
from app.core.schemas.user import UserId
from app.infrastructure.database.models import RefreshToken

from .base_repository import SqlAlchemyRepository


class RevokedRefreshToken(NamedTuple):
    id: UUID
    user_id: UserId
    family_id: UUID


class RefreshTokenRepository(SqlAlchemyRepository):
    async def create_refresh_token(
        self,
        user_id: UUID,
        token_hash: str,
        family_id: UUID,
        expires_at: datetime,
        replaced_by_id: UUID | None = None,
    ) -> UUID:

        query = (
            insert(RefreshToken)
            .values(
                user_id=user_id,
                token_hash=token_hash,
                family_id=family_id,
                expires_at=expires_at,
                replaced_by_id=replaced_by_id,
            )
            .returning(RefreshToken.id)
        )

        token_id = (await self.session.execute(query)).scalar_one()

        return token_id

    async def revoke_active_by_hash(
        self, token_hash: str
    ) -> RevokedRefreshToken | None:
        query = (
            update(RefreshToken)
            .values(revoked_at=func.now())
            .where(
                RefreshToken.revoked_at.is_(None),
                RefreshToken.token_hash == token_hash,
                RefreshToken.expires_at > func.now(),
            )
            .returning(RefreshToken.id, RefreshToken.user_id, RefreshToken.family_id)
        )

        res = (await self.session.execute(query)).mappings().one_or_none()

        if res is not None:
            return RevokedRefreshToken(**res)

        return None

    async def find_token_by_hash(self, token_hash: str) -> RefreshTokenSchema | None:
        query = select(RefreshToken).where(RefreshToken.token_hash == token_hash)

        res = (await self.session.execute(query)).scalar_one_or_none()

        if res is not None:
            return RefreshTokenSchema.model_validate(res)

        return None

    async def set_replaced_by(self, old_token_id: UUID, new_token_id: UUID) -> None:
        query = (
            update(RefreshToken)
            .values(replaced_by_id=new_token_id)
            .where(RefreshToken.id == old_token_id)
        )

        await self.session.execute(query)

    async def revoke_family(self, family_id: UUID) -> int:
        query = (
            update(RefreshToken)
            .values(revoked_at=func.now())
            .where(
                RefreshToken.family_id == family_id,
                RefreshToken.expires_at > func.now(),
                RefreshToken.revoked_at.is_(None),
            )
            .returning(RefreshToken.id)
        )

        res = len((await self.session.execute(query)).scalars().all())

        return res
