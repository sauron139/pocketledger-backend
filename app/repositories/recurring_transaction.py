import uuid
from datetime import date

from dateutil.relativedelta import relativedelta
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import RecurringTransaction, Transaction
from app.repositories.base import BaseRepository


class RecurringTransactionRepository(BaseRepository[RecurringTransaction]):
    def __init__(self, db: AsyncSession):
        super().__init__(RecurringTransaction, db)

    async def get_by_id(self, id: uuid.UUID) -> RecurringTransaction | None:
        result = await self.db.execute(
            select(RecurringTransaction)
            .where(RecurringTransaction.id == id, RecurringTransaction.is_deleted == False)
            .options(selectinload(RecurringTransaction.category))
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> RecurringTransaction:
        instance = RecurringTransaction(**data)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return await self.get_by_id(instance.id)

    async def get_all_for_user(self, user_id: uuid.UUID) -> list[RecurringTransaction]:
        result = await self.db.execute(
            select(RecurringTransaction)
            .where(
                RecurringTransaction.user_id == user_id,
                RecurringTransaction.is_deleted == False,
            )
            .options(selectinload(RecurringTransaction.category))
        )
        return list(result.scalars().all())

    async def get_due(self, today: date) -> list[RecurringTransaction]:
        result = await self.db.execute(
            select(RecurringTransaction)
            .where(
                RecurringTransaction.next_run_date <= today,
                RecurringTransaction.is_active == True,
                RecurringTransaction.is_deleted == False,
                or_(
                    RecurringTransaction.end_date == None,
                    RecurringTransaction.end_date >= today,
                ),
            )
            .options(selectinload(RecurringTransaction.category))
        )
        return list(result.scalars().all())

    async def already_materialized(self, recurring_id: uuid.UUID, for_date: date) -> bool:
        result = await self.db.execute(
            select(Transaction.id).where(
                Transaction.recurring_transaction_id == recurring_id,
                Transaction.transaction_date == for_date,
                Transaction.source == "recurring",
                Transaction.is_deleted == False,
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def advance(self, template: RecurringTransaction, delta: relativedelta) -> None:
        await self.db.execute(
            update(RecurringTransaction)
            .where(RecurringTransaction.id == template.id)
            .values(next_run_date=template.next_run_date + delta)
        )
        await self.db.commit()