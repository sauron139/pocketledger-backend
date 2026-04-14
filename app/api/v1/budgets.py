import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models import User
from app.schemas import APIResponse, BudgetResponse, CreateBudgetRequest, UpdateBudgetRequest
from app.services.budget import BudgetService

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.get("/")
async def list_budgets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = BudgetService(db)
    budgets = await service.list(current_user)
    return APIResponse(data=[BudgetResponse.model_validate(b) for b in budgets])


@router.post("/")
async def create_budget(
    body: CreateBudgetRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = BudgetService(db)
    budget = await service.create(current_user, body.model_dump())
    return APIResponse(data=BudgetResponse.model_validate(budget))


@router.get("/{id}")
async def get_budget(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = BudgetService(db)
    budget = await service.get(current_user, id)
    return APIResponse(data=BudgetResponse.model_validate(budget))


@router.patch("/{id}")
async def update_budget(
    id: uuid.UUID,
    body: UpdateBudgetRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = BudgetService(db)
    budget = await service.update(current_user, id, body.model_dump())
    return APIResponse(data=BudgetResponse.model_validate(budget))


@router.delete("/{id}")
async def delete_budget(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = BudgetService(db)
    await service.delete(current_user, id)
    return APIResponse(data=None, message="Budget deleted")
