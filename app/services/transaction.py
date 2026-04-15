import uuid
from datetime import date
from decimal import Decimal

import redis.asyncio as aioredis
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models import User
from app.repositories.audit_log import AuditLogRepository
from app.repositories.transaction import TransactionRepository
from app.services.notification import NotificationService
from app.services.rate import RateService


class TransactionService:
    def __init__(self, db: AsyncSession, redis: aioredis.Redis):
        self.db = db
        self.repo = TransactionRepository(db)
        self.rate_service = RateService(db, redis)
        self.audit_repo = AuditLogRepository(db)

    async def get(self, user: User, id: uuid.UUID):
        tx = await self.repo.get_by_id(id)
        if not tx:
            raise NotFoundError("Transaction not found")
        if tx.user_id != user.id:
            raise ForbiddenError()
        return tx

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
        background_tasks: BackgroundTasks | None = None,
        source: str = "manual",
        recurring_transaction_id: uuid.UUID | None = None,
    ):
        rate, _ = await self.rate_service.get_rate(currency, user.base_currency, user.id)
        amount_in_base = (amount * rate).quantize(Decimal("0.01"))

        tx = await self.repo.create({
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
            "recurring_transaction_id": recurring_transaction_id,
        })

        if type == "expense" and background_tasks is not None:
            background_tasks.add_task(
                self._check_budget_thresholds, user.id, category_id
            )

        return tx

    async def _check_budget_thresholds(
        self, user_id: uuid.UUID, category_id: uuid.UUID
    ) -> None:
        service = NotificationService(self.db)
        await service.check_budget_thresholds(user_id, category_id)

    async def update(self, user: User, id: uuid.UUID, data: dict):
        tx = await self.repo.get_by_id(id)
        if not tx:
            raise NotFoundError("Transaction not found")
        if tx.user_id != user.id:
            raise ForbiddenError()

        changes = {k: v for k, v in data.items() if v is not None}
        audit_entries = [
            {
                "transaction_id": tx.id,
                "changed_by": user.id,
                "field": field,
                "old_value": str(getattr(tx, field, None)),
                "new_value": str(value),
            }
            for field, value in changes.items()
            if getattr(tx, field, None) != value
        ]

        if audit_entries:
            await self.audit_repo.bulk_create(audit_entries)

        return await self.repo.update(id, changes)

    async def delete(self, user: User, id: uuid.UUID) -> None:
        tx = await self.repo.get_by_id(id)
        if not tx:
            raise NotFoundError("Transaction not found")
        if tx.user_id != user.id:
            raise ForbiddenError()
        await self.repo.soft_delete(id)