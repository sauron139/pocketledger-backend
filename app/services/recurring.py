import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models import RecurringTransaction, User
from app.repositories.recurring_transaction import RecurringTransactionRepository


class RecurringTransactionService:
    def __init__(self, db: AsyncSession):
        self.repo = RecurringTransactionRepository(db)

    async def list(self, user: User) -> list[RecurringTransaction]:
        return await self.repo.get_all_for_user(user.id)

    async def create(self, user: User, data: dict) -> RecurringTransaction:
        return await self.repo.create({"user_id": user.id, **data})

    async def update(self, user: User, id: uuid.UUID, data: dict) -> RecurringTransaction:
        template = await self.repo.get_by_id(id)
        if not template:
            raise NotFoundError("Recurring transaction not found")
        if template.user_id != user.id:
            raise ForbiddenError()
        return await self.repo.update(id, {k: v for k, v in data.items() if v is not None})

    async def delete(self, user: User, id: uuid.UUID) -> None:
        template = await self.repo.get_by_id(id)
        if not template:
            raise NotFoundError("Recurring transaction not found")
        if template.user_id != user.id:
            raise ForbiddenError()
        await self.repo.soft_delete(id)