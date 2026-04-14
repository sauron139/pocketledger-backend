import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ExchangeRateSnapshot


class ExchangeRateSnapshotRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: uuid.UUID, from_currency: str, to_currency: str, rate: Decimal) -> None:
        snapshot = ExchangeRateSnapshot(
            user_id=user_id,
            from_currency=from_currency,
            to_currency=to_currency,
            rate=rate,
        )
        self.db.add(snapshot)
        await self.db.commit()
