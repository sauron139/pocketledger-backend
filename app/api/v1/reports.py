from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models import User
from app.schemas import APIResponse
from app.services.budget import BudgetService
from app.services.report import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary")
async def summary(
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    result = await service.summary(current_user, start_date, end_date)
    return APIResponse(data=result)


@router.get("/by-category")
async def by_category(
    start_date: date = Query(...),
    end_date: date = Query(...),
    type: str = Query("expense"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    result = await service.by_category(current_user, start_date, end_date, type)
    return APIResponse(data=result)


@router.get("/trend")
async def trend(
    start_date: date = Query(...),
    end_date: date = Query(...),
    group_by: str = Query("month"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    result = await service.trend(current_user, start_date, end_date, group_by)
    return APIResponse(data=result)


@router.get("/budget-status")
async def budget_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = BudgetService(db)
    budgets = await service.list(current_user)
    budgets_sorted = sorted(
        budgets,
        key=lambda b: b.utilisation.percentage if b.utilisation else 0,
        reverse=True,
    )
    from app.schemas import BudgetResponse
    return APIResponse(data=[BudgetResponse.model_validate(b) for b in budgets_sorted])
