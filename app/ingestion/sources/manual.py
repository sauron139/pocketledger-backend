from datetime import date
from decimal import Decimal

from app.ingestion.pipeline import TransactionPayload


def build_manual_payload(
    type: str,
    amount: Decimal,
    currency: str,
    category_id: str,
    transaction_date: date,
    description: str | None = None,
) -> TransactionPayload:
    """
    Adapts a manual API request into a normalised TransactionPayload.
    Future adapters (sms.py, mono.py) follow the same contract.
    """
    return TransactionPayload(
        type=type,
        amount=amount,
        currency=currency,
        category_id=category_id,
        transaction_date=transaction_date,
        description=description,
        source="manual",
    )
