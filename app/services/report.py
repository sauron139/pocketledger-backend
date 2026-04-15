from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Category, Transaction, User
from app.schemas import CategoryBreakdownItem, CategoryResponse, SummaryResponse, TrendGroup, TrendResponse
from app.utils.period import compute_current_period, compute_previous_period
from app.schemas import ComparisonResponse, PeriodBounds, PeriodDelta



class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def summary(self, user: User, start_date: date, end_date: date) -> SummaryResponse:
        result = await self.db.execute(
            select(
                Transaction.type,
                func.coalesce(func.sum(Transaction.amount_in_base), 0).label("total"),
            )
            .where(
                Transaction.user_id == user.id,
                Transaction.is_deleted == False,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
            .group_by(Transaction.type)
        )
        rows = result.all()
        totals = {row.type: Decimal(str(row.total)) for row in rows}
        income = totals.get("income", Decimal("0"))
        expense = totals.get("expense", Decimal("0"))
        return SummaryResponse(
            currency=user.base_currency,
            total_income=income,
            total_expense=expense,
            net_cashflow=income - expense,
        )

    async def by_category(self, user: User, start_date: date, end_date: date, type: str = "expense") -> list[CategoryBreakdownItem]:
        result = await self.db.execute(
            select(
                Transaction.category_id,
                func.coalesce(func.sum(Transaction.amount_in_base), 0).label("total"),
            )
            .where(
                Transaction.user_id == user.id,
                Transaction.is_deleted == False,
                Transaction.type == type,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
            .group_by(Transaction.category_id)
            .order_by(func.sum(Transaction.amount_in_base).desc())
        )
        rows = result.all()
        if not rows:
            return []

        grand_total = sum(Decimal(str(r.total)) for r in rows)
        category_ids = [r.category_id for r in rows]

        cats_result = await self.db.execute(
            select(Category).where(Category.id.in_(category_ids))
        )
        cats = {c.id: c for c in cats_result.scalars().all()}

        return [
            CategoryBreakdownItem(
                category=CategoryResponse.model_validate(cats[row.category_id]),
                total=Decimal(str(row.total)),
                percentage=float((Decimal(str(row.total)) / grand_total * 100).quantize(Decimal("0.1"))) if grand_total else 0.0,
            )
            for row in rows if row.category_id in cats
        ]

    async def trend(self, user: User, start_date: date, end_date: date, group_by: str = "month") -> TrendResponse:
        if group_by == "day":
            trunc = func.date_trunc("day", Transaction.transaction_date)
            label_format = "DD Mon YYYY"
        elif group_by == "week":
            trunc = func.date_trunc("week", Transaction.transaction_date)
            label_format = "DD Mon YYYY"
        else:
            trunc = func.date_trunc("month", Transaction.transaction_date)
            label_format = "Mon YYYY"

        result = await self.db.execute(
            select(
                trunc.label("period"),
                Transaction.type,
                func.coalesce(func.sum(Transaction.amount_in_base), 0).label("total"),
            )
            .where(
                Transaction.user_id == user.id,
                Transaction.is_deleted == False,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
            .group_by("period", Transaction.type)
            .order_by("period")
        )
        rows = result.all()

        periods: dict[str, dict] = {}
        for row in rows:
            label = row.period.strftime("%b %Y" if group_by == "month" else "%d %b %Y")
            if label not in periods:
                periods[label] = {"income": Decimal("0"), "expense": Decimal("0")}
            periods[label][row.type] = Decimal(str(row.total))

        groups = [
            TrendGroup(
                label=label,
                income=vals["income"],
                expense=vals["expense"],
                net=vals["income"] - vals["expense"],
            )
            for label, vals in periods.items()
        ]
        return TrendResponse(currency=user.base_currency, groups=groups)

    async def comparison(self, user: User, period: str = "monthly") -> ComparisonResponse:
        current_start, current_end = compute_current_period(period)
        previous_start, previous_end = compute_previous_period(period)

        current = await self.summary(user, current_start, current_end)
        previous = await self.summary(user, previous_start, previous_end)

        def delta(current_val: Decimal, previous_val: Decimal) -> dict:
            absolute = current_val - previous_val
            percentage = (
                float((absolute / previous_val * 100).quantize(Decimal("0.1")))
                if previous_val != 0
                else None
            )
            return {"absolute": absolute, "percentage": percentage}

        return ComparisonResponse(
            currency=user.base_currency,
            period=period,
            current_period=PeriodBounds(start=current_start, end=current_end),
            previous_period=PeriodBounds(start=previous_start, end=previous_end),
            income=PeriodDelta(
                current=current.total_income,
                previous=previous.total_income,
                **delta(current.total_income, previous.total_income),
            ),
            expense=PeriodDelta(
                current=current.total_expense,
                previous=previous.total_expense,
                **delta(current.total_expense, previous.total_expense),
            ),
            net=PeriodDelta(
                current=current.net_cashflow,
                previous=previous.net_cashflow,
                **delta(current.net_cashflow, previous.net_cashflow),
            ),
        )

