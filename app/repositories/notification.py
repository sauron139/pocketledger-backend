import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, db: AsyncSession):
        super().__init__(Notification, db)

    async def get_unread_for_user(self, user_id: uuid.UUID) -> list[Notification]:
        result = await self.db.execute(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read == False,
                Notification.is_deleted == False,
            ).order_by(Notification.created_at.desc())
        )
        return list(result.scalars().all())

    async def exists(self, budget_id: uuid.UUID, threshold: int, period_start: date) -> bool:
        result = await self.db.execute(
            select(Notification.id).where(
                Notification.budget_id == budget_id,
                Notification.threshold == threshold,
                Notification.created_at >= period_start,
                Notification.is_deleted == False,
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None