import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models import User
from app.repositories.category import CategoryRepository


class CategoryService:
    def __init__(self, db: AsyncSession):
        self.repo = CategoryRepository(db)

    async def list(self, user: User, type: str | None = None):
        return await self.repo.get_all_for_user(user.id, type=type)

    async def create(self, user: User, name: str, type: str, icon: str | None):
        return await self.repo.create({
            "user_id": user.id,
            "name": name,
            "type": type,
            "icon": icon,
            "is_default": False,
        })

    async def update(self, user: User, id: uuid.UUID, data: dict):
        category = await self.repo.get_by_id(id)
        if not category:
            raise NotFoundError("Category not found")
        if category.user_id != user.id:
            raise ForbiddenError()
        return await self.repo.update(id, {k: v for k, v in data.items() if v is not None})

    async def delete(self, user: User, id: uuid.UUID) -> None:
        category = await self.repo.get_by_id(id)
        if not category:
            raise NotFoundError("Category not found")
        if category.user_id != user.id:
            raise ForbiddenError()
        if await self.repo.has_linked_transactions(id):
            raise ConflictError("Category has linked transactions — reassign them before deleting")
        if await self.repo.has_active_budget(id):
            raise ConflictError("Category has an active budget — delete it before deleting this category")
        await self.repo.soft_delete(id)
