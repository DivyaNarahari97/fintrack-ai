from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class StatementOut(BaseModel):
    id: UUID
    filename: str
    file_type: str
    uploaded_at: datetime
    status: str
    error_message: str | None = None

    model_config = {"from_attributes": True}


class TransactionOut(BaseModel):
    id: UUID
    statement_id: UUID
    date: date
    description: str
    amount: Decimal
    currency: str
    category: str | None = None

    model_config = {"from_attributes": True}


class TransactionPage(BaseModel):
    items: list[TransactionOut]
    total: int
    page: int
    page_size: int


class CategoryTotal(BaseModel):
    category: str
    total: Decimal
    count: int


class MonthlyTotal(BaseModel):
    month: str  # "2024-06"
    total: Decimal


class SummaryOut(BaseModel):
    by_category: list[CategoryTotal]
    by_month: list[MonthlyTotal]
    total_spent: Decimal
    top_merchants: list[dict]


class ChatRequest(BaseModel):
    message: str


class UploadResponse(BaseModel):
    statement_id: UUID
    status: str
