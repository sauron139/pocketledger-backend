import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.budget import BudgetRepository
from app.repositories.notification import NotificationRepository
from app.repositories.transaction import TransactionRepository
from app.utils.period import compute_period_bounds

THRESHOLDS = [80, 100]


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.budget_repo = BudgetRepository(db)
        self.tx_repo = TransactionRepository(db)
        self.notification_repo = NotificationRepository(db)

    async def check_budget_thresholds(
        self,
        user_id: uuid.UUID,
        category_id: uuid.UUID,
    ) -> None:
        budgets = await self.budget_repo.get_active_for_category(user_id, category_id)

        for budget in budgets:
            period_start, period_end = compute_period_bounds(budget.start_date, budget.period)
            spent = await self.tx_repo.get_total_by_category_in_period(
                user_id, budget.category_id, period_start, period_end
            )
            if budget.amount == 0:
                continue

            percentage = float((spent / budget.amount * 100).quantize(Decimal("0.1")))

            for threshold in THRESHOLDS:
                if percentage >= threshold:
                    already_notified = await self.notification_repo.exists(
                        budget.id, threshold, period_start
                    )
                    if not already_notified:
                        await self.notification_repo.create({
                            "user_id": user_id,
                            "budget_id": budget.id,
                            "threshold": threshold,
                            "percentage": percentage,
                            "is_read": False,
                        })