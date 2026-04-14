import uuid
from typing import Any, Generic, Type, TypeVar

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: uuid.UUID) -> ModelType | None:
        result = await self.db.execute(
            select(self.model).where(self.model.id == id, self.model.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def get_all(self, **filters) -> list[ModelType]:
        query = select(self.model).where(self.model.is_deleted == False)
        for key, value in filters.items():
            query = query.where(getattr(self.model, key) == value)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, data: dict[str, Any]) -> ModelType:
        instance = self.model(**data)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def update(self, id: uuid.UUID, data: dict[str, Any]) -> ModelType | None:
        await self.db.execute(
            update(self.model)
            .where(self.model.id == id, self.model.is_deleted == False)
            .values(**data)
        )
        await self.db.commit()
        return await self.get_by_id(id)

    async def soft_delete(self, id: uuid.UUID) -> bool:
        await self.db.execute(
            update(self.model)
            .where(self.model.id == id, self.model.is_deleted == False)
            .values(is_deleted=True)
        )
        await self.db.commit()
        return True
