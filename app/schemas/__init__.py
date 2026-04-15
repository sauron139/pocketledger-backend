import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, EmailStr

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    status: str = "success"
    data: T
    message: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    total: int
    page: int
    limit: int


# --- Auth ---

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    base_currency: str = "NGN"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str


class RefreshRequest(BaseModel):
    refresh_token: str


# --- User ---

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    base_currency: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateUserRequest(BaseModel):
    email: Optional[EmailStr] = None
    base_currency: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# --- Category ---

class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    icon: Optional[str]
    is_default: bool

    class Config:
        from_attributes = True


class CreateCategoryRequest(BaseModel):
    name: str
    type: str
    icon: Optional[str] = None


class UpdateCategoryRequest(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    icon: Optional[str] = None


# --- Transaction ---

class TransactionResponse(BaseModel):
    id: uuid.UUID
    type: str
    amount: Decimal
    currency: str
    exchange_rate_to_base: Decimal
    amount_in_base: Decimal
    description: Optional[str]
    source: str
    transaction_date: date
    category: CategoryResponse
    created_at: datetime

    class Config:
        from_attributes = True


class CreateTransactionRequest(BaseModel):
    type: str
    amount: Decimal
    currency: str
    category_id: uuid.UUID
    description: Optional[str] = None
    transaction_date: date


class UpdateTransactionRequest(BaseModel):
    description: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    transaction_date: Optional[date] = None


# --- Budget ---

class UtilisationSchema(BaseModel):
    spent: Decimal
    remaining: Decimal
    percentage: float
    period_start: date
    period_end: date


class BudgetResponse(BaseModel):
    id: uuid.UUID
    amount: Decimal
    currency: str
    period: str
    start_date: date
    is_recurring: bool
    category: CategoryResponse
    utilisation: Optional[UtilisationSchema] = None

    class Config:
        from_attributes = True


class CreateBudgetRequest(BaseModel):
    category_id: uuid.UUID
    amount: Decimal
    currency: str
    period: str = "monthly"
    start_date: date
    is_recurring: bool = True


class UpdateBudgetRequest(BaseModel):
    amount: Optional[Decimal] = None
    period: Optional[str] = None
    is_recurring: Optional[bool] = None


# --- Reports ---

class SummaryResponse(BaseModel):
    currency: str
    total_income: Decimal
    total_expense: Decimal
    net_cashflow: Decimal


class CategoryBreakdownItem(BaseModel):
    category: CategoryResponse
    total: Decimal
    percentage: float


class TrendGroup(BaseModel):
    label: str
    income: Decimal
    expense: Decimal
    net: Decimal


class TrendResponse(BaseModel):
    currency: str
    groups: list[TrendGroup]


# --- Exchange Rate ---

class RateResponse(BaseModel):
    from_currency: str
    to_currency: str
    rate: Decimal
    cached: bool

class PeriodBounds(BaseModel):
    start: date
    end: date


class PeriodDelta(BaseModel):
    current: Decimal
    previous: Decimal
    absolute: Decimal
    percentage: float | None


class ComparisonResponse(BaseModel):
    currency: str
    period: str
    current_period: PeriodBounds
    previous_period: PeriodBounds
    income: PeriodDelta
    expense: PeriodDelta
    net: PeriodDelta

class RecurringTransactionResponse(BaseModel):
    id: uuid.UUID
    type: str
    amount: Decimal
    currency: str
    description: Optional[str]
    frequency: str
    next_run_date: date
    end_date: Optional[date]
    is_active: bool
    category: CategoryResponse

    class Config:
        from_attributes = True


class CreateRecurringTransactionRequest(BaseModel):
    type: str
    amount: Decimal
    currency: str
    category_id: uuid.UUID
    description: Optional[str] = None
    frequency: str
    next_run_date: date
    end_date: Optional[date] = None