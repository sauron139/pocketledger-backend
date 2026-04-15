import uuid

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.repositories.category import CategoryRepository
from app.repositories.user import UserRepository
from app.schemas import TokenResponse

from app.core.logging import get_logger

logger = get_logger("auth")

class AuthService:
    def __init__(self, db: AsyncSession, redis: aioredis.Redis):
        self.db = db
        self.redis = redis
        self.user_repo = UserRepository(db)
        self.category_repo = CategoryRepository(db)

    async def register(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        base_currency: str,
        middle_name: str | None = None,
        phone_number: str | None = None,
        address: str | None = None,
    ) -> tuple[dict, TokenResponse]:
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ConflictError("Email already registered")

        user = await self.user_repo.create({
            "email": email,
            "hashed_password": hash_password(password),
            "first_name": first_name,
            "last_name": last_name,
            "middle_name": middle_name,
            "phone_number": phone_number,
            "address": address,
            "base_currency": base_currency,
            "role": "user",
        })

        await self.category_repo.seed_defaults_for_user(user.id)
        tokens = await self._issue_tokens(user.id)
        return user, tokens

    async def login(self, email: str, password: str) -> tuple[dict, TokenResponse]:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid credentials")

        if user.is_deleted:
            raise UnauthorizedError("Account has been deactivated")
        tokens = await self._issue_tokens(user.id)
        logger.info("auth.login_success", user_id=str(user.id))
        return user, tokens

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid refresh token")

        user_id = payload.get("sub")
        stored = await self.redis.get(f"refresh:{user_id}")
        if not stored or stored != refresh_token:
            raise UnauthorizedError("Refresh token has been revoked")

        return TokenResponse(
            access_token=create_access_token(user_id),
            refresh_token=refresh_token,
        )

    async def logout(self, user_id: uuid.UUID) -> None:
        await self.redis.delete(f"refresh:{str(user_id)}")

    async def _issue_tokens(self, user_id: uuid.UUID) -> TokenResponse:
        access = create_access_token(str(user_id))
        refresh = create_refresh_token(str(user_id))
        await self.redis.setex(
            f"refresh:{str(user_id)}",
            settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            refresh,
        )
        return TokenResponse(access_token=access, refresh_token=refresh)
