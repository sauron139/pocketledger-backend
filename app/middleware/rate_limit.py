import time
import redis.asyncio as aioredis
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window = 60

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in ("/health", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        identity = self._get_identity(request)
        key = f"rate:{identity}:{request.url.path}"

        now = time.time()
        window_start = now - self.window

        async with redis.pipeline() as pipe:
            await pipe.zremrangebyscore(key, 0, window_start)
            await pipe.zcard(key)
            await pipe.zadd(key, {str(now): now})
            await pipe.expire(key, self.window)
            results = await pipe.execute()

        request_count = results[1]

        if request_count >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"status": "error", "message": "Too many requests"},
                headers={"Retry-After": str(self.window)},
            )

        return await call_next(request)

    def _get_identity(self, request: Request) -> str:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth.split(" ")[1]
            return f"token:{token[:16]}"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        return f"ip:{request.client.host}"