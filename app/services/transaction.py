import uuid
from datetime import date
from decimal import Decimal

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models import User
from app.repositories.transaction import TransactionRepository
from app.services.rate import RateService


class TransactionService:
    def __init__(self, db: AsyncSession, redis: aioredis.Redis):
        self.db = db
        self.repo = TransactionRepository(db)
        self.rate_service = RateService(db, redis)

    async def list(self, user: User, **filters) -> tuple[list, int]:
        return await self.repo.get_paginated(user_id=user.id, **filters)

    async def create(
        self,
        user: User,
        type: str,
        amount: Decimal,
        currency: str,
        category_id: uuid.UUID,
        description: str | None,
        transaction_date: date,
        source: str = "manual",
    ):
        rate, _ = await self.rate_service.get_rate(currency, user.base_currency, user.id)
        amount_in_base = (amount * rate).quantize(Decimal("0.01"))

        return await self.repo.create({
            "user_id": user.id,
            "type": type,
            "amount": amount,
            "currency": currency,
            "exchange_rate_to_base": rate,
            "amount_in_base": amount_in_base,
            "category_id": category_id,
            "description": description,
            "transaction_date": transaction_date,
            "source": source,
        })

    async def update(self, user: User, id: uuid.UUID, data: dict):
        tx = await self.repo.get_by_id(id)
        if not tx:
            raise NotFoundError("Transaction not found")
        if tx.user_id != user.id:
            raise ForbiddenError()
        return await self.repo.update(id, {k: v for k, v in data.items() if v is not None})

    async def delete(self, user: User, id: uuid.UUID) -> None:
        tx = await self.repo.get_by_id(id)
        if not tx:
            raise NotFoundError("Transaction not found")
        if tx.user_id != user.id:
            raise ForbiddenError()
        await self.repo.soft_delete(id)
