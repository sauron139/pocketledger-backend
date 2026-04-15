import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models import User
from app.schemas import APIResponse, CreateRecurringTransactionRequest, RecurringTransactionResponse
from app.services.recurring import RecurringTransactionService

router = APIRouter(prefix="/recurring", tags=["recurring"])


@router.get("/")
async def list_recurring(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RecurringTransactionService(db)
    templates = await service.list(current_user)
    return APIResponse(data=[RecurringTransactionResponse.model_validate(t) for t in templates])


@router.post("/")
async def create_recurring(
    body: CreateRecurringTransactionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RecurringTransactionService(db)
    template = await service.create(current_user, body.model_dump())
    return APIResponse(data=RecurringTransactionResponse.model_validate(template))


@router.patch("/{id}")
async def update_recurring(
    id: uuid.UUID,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RecurringTransactionService(db)
    template = await service.update(current_user, id, body)
    return APIResponse(data=RecurringTransactionResponse.model_validate(template))


@router.delete("/{id}")
async def delete_recurring(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RecurringTransactionService(db)
    await service.delete(current_user, id)
    return APIResponse(data=None, message="Recurring transaction deleted")