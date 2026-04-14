import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, get_redis
from app.models import User
from app.schemas import APIResponse, RateResponse
from app.services.rate import RateService

router = APIRouter(prefix="/rates", tags=["rates"])


@router.get("/current")
async def get_current_rate(
    from_currency: str = Query(...),
    to_currency: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    service = RateService(db, redis)
    rate, cached = await service.get_rate(from_currency, to_currency, current_user.id)
    return APIResponse(
        data=RateResponse(
            from_currency=from_currency,
            to_currency=to_currency,
            rate=rate,
            cached=cached,
        )
    )
