import uuid
from datetime import date
from typing import Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, get_redis
from app.models import User
from app.schemas import (
    APIResponse,
    CreateTransactionRequest,
    PaginatedResponse,
    TransactionResponse,
    UpdateTransactionRequest,
)
from app.services.transaction import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/")
async def list_transactions(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    type: Optional[str] = Query(None),
    category_id: Optional[uuid.UUID] = Query(None),
    currency: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    service = TransactionService(db, redis)
    transactions, total = await service.list(
        current_user,
        start_date=start_date,
        end_date=end_date,
        type=type,
        category_id=category_id,
        currency=currency,
        source=source,
        page=page,
        limit=limit,
    )
    return APIResponse(
        data=PaginatedResponse(
            data=[TransactionResponse.model_validate(t) for t in transactions],
            total=total,
            page=page,
            limit=limit,
        )
    )


@router.post("/")
async def create_transaction(
    body: CreateTransactionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    service = TransactionService(db, redis)
    tx = await service.create(
        current_user,
        type=body.type,
        amount=body.amount,
        currency=body.currency,
        category_id=body.category_id,
        description=body.description,
        transaction_date=body.transaction_date,
    )
    return APIResponse(data=TransactionResponse.model_validate(tx))


@router.get("/{id}")
async def get_transaction(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    service = TransactionService(db, redis)
    tx = await service.repo.get_by_id(id)
    from app.core.exceptions import ForbiddenError, NotFoundError
    if not tx:
        raise NotFoundError("Transaction not found")
    if tx.user_id != current_user.id:
        raise ForbiddenError()
    return APIResponse(data=TransactionResponse.model_validate(tx))


@router.patch("/{id}")
async def update_transaction(
    id: uuid.UUID,
    body: UpdateTransactionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    service = TransactionService(db, redis)
    tx = await service.update(current_user, id, body.model_dump())
    return APIResponse(data=TransactionResponse.model_validate(tx))


@router.delete("/{id}")
async def delete_transaction(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    service = TransactionService(db, redis)
    await service.delete(current_user, id)
    return APIResponse(data=None, message="Transaction deleted")
