from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date


class CustomerBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    credit_limit: float = 0.0
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    credit_limit: Optional[float] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerResponse(CustomerBase):
    id: int
    customer_code: Optional[str] = None
    outstanding_balance: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class QuotationItemBase(BaseModel):
    product_id: Optional[int] = None
    description: str
    quantity: float
    unit_price: float
    discount: float = 0.0
    tax_rate: float = 0.0


class QuotationItemCreate(QuotationItemBase):
    pass


class QuotationItemResponse(QuotationItemBase):
    id: int
    tax_amount: float
    total: float

    class Config:
        from_attributes = True


class QuotationBase(BaseModel):
    customer_id: int
    date: date
    valid_until: Optional[date] = None
    terms: Optional[str] = None
    notes: Optional[str] = None


class QuotationCreate(QuotationBase):
    items: List[QuotationItemCreate]


class QuotationUpdate(BaseModel):
    customer_id: Optional[int] = None
    date: Optional[date] = None
    valid_until: Optional[date] = None
    status: Optional[str] = None
    terms: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[QuotationItemCreate]] = None


class QuotationResponse(QuotationBase):
    id: int
    quotation_number: str
    status: str
    subtotal: float
    discount: float
    tax_amount: float
    total: float
    created_at: datetime
    items: List[QuotationItemResponse] = []
    customer: Optional[CustomerResponse] = None

    class Config:
        from_attributes = True


class InvoiceItemBase(BaseModel):
    product_id: Optional[int] = None
    description: str
    quantity: float
    unit_price: float
    discount: float = 0.0
    tax_rate: float = 0.0


class InvoiceItemCreate(InvoiceItemBase):
    pass


class InvoiceItemResponse(InvoiceItemBase):
    id: int
    tax_amount: float
    total: float

    class Config:
        from_attributes = True


class InvoiceBase(BaseModel):
    customer_id: int
    quotation_id: Optional[int] = None
    date: date
    due_date: Optional[date] = None
    terms: Optional[str] = None
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    items: List[InvoiceItemCreate]


class InvoiceUpdate(BaseModel):
    customer_id: Optional[int] = None
    date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    terms: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[InvoiceItemCreate]] = None


class InvoiceResponse(InvoiceBase):
    id: int
    invoice_number: str
    status: str
    subtotal: float
    discount: float
    tax_amount: float
    total: float
    paid_amount: float
    balance_due: float
    created_at: datetime
    items: List[InvoiceItemResponse] = []
    customer: Optional[CustomerResponse] = None

    class Config:
        from_attributes = True


class PaymentBase(BaseModel):
    invoice_id: int
    customer_id: int
    amount: float
    payment_date: date
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentResponse(PaymentBase):
    id: int
    payment_number: str
    created_at: datetime

    class Config:
        from_attributes = True
