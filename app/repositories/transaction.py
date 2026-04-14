import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Transaction
from app.repositories.base import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, db: AsyncSession):
        super().__init__(Transaction, db)

    async def get_by_id(self, id: uuid.UUID) -> Transaction | None:
        result = await self.db.execute(
            select(Transaction)
            .where(Transaction.id == id, Transaction.is_deleted == False)
            .options(selectinload(Transaction.category))
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> Transaction:
        instance = Transaction(**data)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return await self.get_by_id(instance.id)

    async def get_paginated(
        self,
        user_id: uuid.UUID,
        start_date: date | None = None,
        end_date: date | None = None,
        type: str | None = None,
        category_id: uuid.UUID | None = None,
        currency: str | None = None,
        source: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Transaction], int]:
        query = (
            select(Transaction)
            .where(Transaction.user_id == user_id, Transaction.is_deleted == False)
            .options(selectinload(Transaction.category))
        )
        if start_date:
            query = query.where(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.where(Transaction.transaction_date <= end_date)
        if type:
            query = query.where(Transaction.type == type)
        if category_id:
            query = query.where(Transaction.category_id == category_id)
        if currency:
            query = query.where(Transaction.currency == currency)
        if source:
            query = query.where(Transaction.source == source)

        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        query = query.order_by(Transaction.transaction_date.desc()).offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_total_by_category_in_period(
        self,
        user_id: uuid.UUID,
        category_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> Decimal:
        result = await self.db.execute(
            select(func.coalesce(func.sum(Transaction.amount_in_base), 0)).where(
                Transaction.user_id == user_id,
                Transaction.category_id == category_id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
                Transaction.is_deleted == False,
                Transaction.type == "expense",
            )
        )
        return result.scalar_one()
