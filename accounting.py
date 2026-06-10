from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


class AccountCategoryBase(BaseModel):
    name: str
    type: str  # income, expense, asset, liability
    description: Optional[str] = None
    is_active: bool = True


class AccountCategoryCreate(AccountCategoryBase):
    pass


class AccountCategoryUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class AccountCategoryResponse(AccountCategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionBase(BaseModel):
    type: str  # income or expense
    category_id: Optional[int] = None
    date: date
    amount: float
    description: str
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class TransactionCreate(TransactionBase):
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None


class TransactionUpdate(BaseModel):
    type: Optional[str] = None
    category_id: Optional[int] = None
    date: Optional[date] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    attachment_url: Optional[str] = None


class TransactionResponse(TransactionBase):
    id: int
    transaction_number: str
    attachment_url: Optional[str] = None
    created_at: datetime
    category: Optional[AccountCategoryResponse] = None

    class Config:
        from_attributes = True


class LedgerEntryBase(BaseModel):
    date: date
    account_name: str
    description: Optional[str] = None
    debit: float = 0.0
    credit: float = 0.0
    balance: float = 0.0


class LedgerEntryCreate(LedgerEntryBase):
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None


class LedgerEntryResponse(LedgerEntryBase):
    id: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FinancialSummary(BaseModel):
    total_income: float
    total_expense: float
    net_profit: float
    income_by_category: List[dict]
    expense_by_category: List[dict]
    monthly_trend: List[dict]
