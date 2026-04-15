import uuid
from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.period import compute_period_bounds
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models import Budget, User
from app.repositories.budget import BudgetRepository
from app.repositories.transaction import TransactionRepository
from app.schemas import UtilisationSchema



class BudgetService:
    def __init__(self, db: AsyncSession):
        self.repo = BudgetRepository(db)
        self.tx_repo = TransactionRepository(db)

    async def list(self, user: User) -> list[Budget]:
        budgets = await self.repo.get_all_for_user(user.id)
        return [await self._attach_utilisation(b, user.id) for b in budgets]

    async def get(self, user: User, id: uuid.UUID) -> Budget:
        budget = await self.repo.get_by_id_for_user(id, user.id)
        if not budget:
            raise NotFoundError("Budget not found")
        return await self._attach_utilisation(budget, user.id)

    async def create(self, user: User, data: dict):
        return await self.repo.create({"user_id": user.id, **data})

    async def update(self, user: User, id: uuid.UUID, data: dict):
        budget = await self.repo.get_by_id_for_user(id, user.id)
        if not budget:
            raise NotFoundError("Budget not found")
        return await self.repo.update(id, {k: v for k, v in data.items() if v is not None})

    async def delete(self, user: User, id: uuid.UUID) -> None:
        budget = await self.repo.get_by_id_for_user(id, user.id)
        if not budget:
            raise NotFoundError("Budget not found")
        await self.repo.soft_delete(id)

    async def _attach_utilisation(self, budget: Budget, user_id: uuid.UUID) -> Budget:
        period_start, period_end = compute_period_bounds(budget.start_date, budget.period)
        spent = await self.tx_repo.get_total_by_category_in_period(
            user_id, budget.category_id, period_start, period_end
        )
        remaining = max(budget.amount - spent, Decimal("0"))
        percentage = float((spent / budget.amount * 100).quantize(Decimal("0.1"))) if budget.amount else 0.0

        # Attach utilisation as a non-mapped attribute so BudgetResponse can read it
        budget.utilisation = UtilisationSchema(
            spent=spent,
            remaining=remaining,
            percentage=percentage,
            period_start=period_start,
            period_end=period_end,
        )
        return budget
