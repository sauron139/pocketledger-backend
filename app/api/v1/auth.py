from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

import redis.asyncio as aioredis
from app.core.dependencies import get_current_user, get_db, get_redis
from app.models import User
from app.schemas import APIResponse, LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    service = AuthService(db, redis)
    user, tokens = await service.register(body.email, body.password, body.base_currency)
    return APIResponse(data={"user": UserResponse.model_validate(user), **tokens.model_dump()})


@router.post("/login")
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    service = AuthService(db, redis)
    user, tokens = await service.login(body.email, body.password)
    return APIResponse(data={"user": UserResponse.model_validate(user), **tokens.model_dump()})


@router.post("/refresh")
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    service = AuthService(db, redis)
    tokens = await service.refresh(body.refresh_token)
    return APIResponse(data=tokens)


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    service = AuthService(db, redis)
    await service.logout(current_user.id)
    return APIResponse(data=None, message="Logged out successfully")
