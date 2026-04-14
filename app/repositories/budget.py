import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Budget
from app.repositories.base import BaseRepository


class BudgetRepository(BaseRepository[Budget]):
    def __init__(self, db: AsyncSession):
        super().__init__(Budget, db)

    async def get_by_id(self, id: uuid.UUID) -> Budget | None:
        result = await self.db.execute(
            select(Budget)
            .where(Budget.id == id, Budget.is_deleted == False)
            .options(selectinload(Budget.category))
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> Budget:
        instance = Budget(**data)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return await self.get_by_id(instance.id)

    async def get_all_for_user(self, user_id: uuid.UUID) -> list[Budget]:
        result = await self.db.execute(
            select(Budget)
            .where(Budget.user_id == user_id, Budget.is_deleted == False)
            .options(selectinload(Budget.category))
        )
        return list(result.scalars().all())

    async def get_by_id_for_user(self, id: uuid.UUID, user_id: uuid.UUID) -> Budget | None:
        result = await self.db.execute(
            select(Budget)
            .where(Budget.id == id, Budget.user_id == user_id, Budget.is_deleted == False)
            .options(selectinload(Budget.category))
        )
        return result.scalar_one_or_none()
