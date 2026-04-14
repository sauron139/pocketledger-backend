import uuid
from decimal import Decimal

import httpx
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.repositories.exchange_rate_snapshot import ExchangeRateSnapshotRepository


class RateService:
    def __init__(self, db: AsyncSession, redis: aioredis.Redis):
        self.db = db
        self.redis = redis
        self.snapshot_repo = ExchangeRateSnapshotRepository(db)

    async def get_rate(self, from_currency: str, to_currency: str, user_id: uuid.UUID) -> tuple[Decimal, bool]:
        if from_currency == to_currency:
            return Decimal("1.0"), True

        cache_key = f"rate:{from_currency}:{to_currency}"
        cached = await self.redis.get(cache_key)

        if cached:
            return Decimal(cached), True

        rate = await self._fetch_from_provider(from_currency, to_currency)
        await self.redis.setex(cache_key, settings.EXCHANGE_RATE_CACHE_TTL, str(rate))
        await self.snapshot_repo.create(user_id, from_currency, to_currency, rate)
        return rate, False

    async def _fetch_from_provider(self, from_currency: str, to_currency: str) -> Decimal:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.EXCHANGE_RATE_API_URL}/latest.json",
                params={"app_id": settings.EXCHANGE_RATE_API_KEY, "base": from_currency, "symbols": to_currency},
            )
            if response.status_code != 200:
                raise AppException(502, "Exchange rate service unavailable")

            data = response.json()
            rate = data.get("rates", {}).get(to_currency)
            if not rate:
                raise AppException(400, f"Unsupported currency pair: {from_currency}/{to_currency}")

            return Decimal(str(rate))
