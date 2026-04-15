import json
import uuid

import redis.asyncio as aioredis
from fastapi import Depends, Header, Request
from fastapi.responses import JSONResponse
from typing import Optional

from app.core.dependencies import get_current_user, get_redis
from app.core.exceptions import BadRequestError
from app.models import User

IDEMPOTENCY_TTL = 86400


async def idempotency_guard(
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    redis: aioredis.Redis = Depends(get_redis),
):
    if idempotency_key is None:
        raise BadRequestError("Idempotency-Key header is required")

    try:
        uuid.UUID(idempotency_key)
    except ValueError:
        raise BadRequestError("Idempotency-Key must be a valid UUID")

    redis_key = f"idempotency:{current_user.id}:{idempotency_key}"
    cached = await redis.get(redis_key)

    if cached:
        return JSONResponse(
            status_code=200,
            content=json.loads(cached),
            headers={"X-Idempotent-Replayed": "true"},
        )

    request.state.idempotency_key = redis_key
    request.state.redis = redis

async def store_idempotent_response(request: Request, response_data: dict) -> None:
    redis_key = getattr(request.state, "idempotency_key", None)
    redis = getattr(request.state, "redis", None)

    if redis_key and redis:
        await redis.setex(redis_key, IDEMPOTENCY_TTL, json.dumps(response_data))