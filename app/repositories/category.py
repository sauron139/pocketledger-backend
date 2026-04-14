import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, DefaultCategory
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, db: AsyncSession):
        super().__init__(Category, db)

    async def get_all_for_user(self, user_id: uuid.UUID, type: str | None = None) -> list[Category]:
        query = select(Category).where(Category.user_id == user_id, Category.is_deleted == False)
        if type:
            query = query.where(Category.type == type)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def has_linked_transactions(self, category_id: uuid.UUID) -> bool:
        from app.models import Transaction
        result = await self.db.execute(
            select(Transaction.id).where(
                Transaction.category_id == category_id,
                Transaction.is_deleted == False,
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def has_active_budget(self, category_id: uuid.UUID) -> bool:
        from app.models import Budget
        result = await self.db.execute(
            select(Budget.id).where(
                Budget.category_id == category_id,
                Budget.is_deleted == False,
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def get_defaults(self) -> list[DefaultCategory]:
        result = await self.db.execute(select(DefaultCategory))
        return list(result.scalars().all())

    async def seed_defaults_for_user(self, user_id: uuid.UUID) -> None:
        defaults = await self.get_defaults()
        for default in defaults:
            category = Category(
                user_id=user_id,
                seeded_from=default.id,
                name=default.name,
                type=default.type,
                icon=default.icon,
                is_default=True,
            )
            self.db.add(category)
        await self.db.commit()
