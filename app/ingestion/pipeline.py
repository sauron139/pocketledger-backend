from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class TransactionPayload:
    """
    Normalised transaction payload consumed by the pipeline regardless of source.
    SMS parser, Mono webhook, or manual entry all produce this shape.
    """
    type: str
    amount: Decimal
    currency: str
    category_id: str
    transaction_date: date
    description: str | None = None
    source: str = "manual"


class IngestionPipeline:
    """
    The pipeline receives a TransactionPayload and persists it.
    Source adapters (manual, sms, mono) are responsible for normalising
    their raw data into a TransactionPayload before calling run().
    """

    def __init__(self, transaction_service):
        self.transaction_service = transaction_service

    async def run(self, user, payload: TransactionPayload):
        return await self.transaction_service.create(
            user=user,
            type=payload.type,
            amount=payload.amount,
            currency=payload.currency,
            category_id=payload.category_id,
            description=payload.description,
            transaction_date=payload.transaction_date,
            source=payload.source,
        )
