import csv
import io
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.repositories.transaction import TransactionRepository


class ExportService:
    def __init__(self, db: AsyncSession):
        self.repo = TransactionRepository(db)

    async def transactions_csv(
        self,
        user: User,
        start_date: date | None = None,
        end_date: date | None = None,
        type: str | None = None,
    ) -> io.StringIO:
        transactions, _ = await self.repo.get_paginated(
            user_id=user.id,
            start_date=start_date,
            end_date=end_date,
            type=type,
            page=1,
            limit=10000,
        )

        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=[
                "id",
                "date",
                "type",
                "category",
                "description",
                "amount",
                "currency",
                "amount_in_base",
                "base_currency",
                "exchange_rate",
                "source",
                "created_at",
            ],
        )
        writer.writeheader()

        for tx in transactions:
            writer.writerow({
                "id": str(tx.id),
                "date": tx.transaction_date.isoformat(),
                "type": tx.type,
                "category": tx.category.name if tx.category else "",
                "description": tx.description or "",
                "amount": str(tx.amount),
                "currency": tx.currency,
                "amount_in_base": str(tx.amount_in_base),
                "base_currency": user.base_currency,
                "exchange_rate": str(tx.exchange_rate_to_base),
                "source": tx.source,
                "created_at": tx.created_at.isoformat(),
            })

        buffer.seek(0)
        return buffer