import uuid
from datetime import date
from decimal import Decimal
from pydantic import BaseModel
from .category import CategoryResponse

class RecurringTransactionResponse(BaseModel):
    id: uuid.UUID
    type: str
    amount: Decimal
    currency: str
    description: str | None
    frequency: str
    next_run_date: date
    end_date: date | None
    is_active: bool
    category: CategoryResponse  # Changed from Any to CategoryResponse

    class Config:
        from_attributes = True


class CreateRecurringTransactionRequest(BaseModel):
    type: str
    amount: Decimal
    currency: str
    category_id: uuid.UUID
    description: str | None = None
    frequency: str
    next_run_date: date
    end_date: date | None = None
