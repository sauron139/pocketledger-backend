from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TransactionAuditLog


class AuditLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def bulk_create(self, entries: list[dict[str, Any]]) -> None:
        self.db.add_all([TransactionAuditLog(**entry) for entry in entries])
        await self.db.commit()