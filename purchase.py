from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


class SupplierBase(BaseModel):
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
    bank_account: Optional[str] = None
    bank_name: Optional[str] = None
    ifsc_code: Optional[str] = None
    credit_terms: int = 30
    notes: Optional[str] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
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
    bank_account: Optional[str] = None
    bank_name: Optional[str] = None
    ifsc_code: Optional[str] = None
    credit_terms: Optional[int] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierResponse(SupplierBase):
    id: int
    supplier_code: Optional[str] = None
    outstanding_balance: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PurchaseOrderItemBase(BaseModel):
    product_id: Optional[int] = None
    description: str
    quantity: float
    unit_price: float
    tax_rate: float = 0.0


class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    pass


class PurchaseOrderItemResponse(PurchaseOrderItemBase):
    id: int
    received_quantity: float
    tax_amount: float
    total: float

    class Config:
        from_attributes = True


class PurchaseOrderBase(BaseModel):
    supplier_id: int
    date: date
    expected_delivery: Optional[date] = None
    terms: Optional[str] = None
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    items: List[PurchaseOrderItemCreate]


class PurchaseOrderUpdate(BaseModel):
    supplier_id: Optional[int] = None
    date: Optional[date] = None
    expected_delivery: Optional[date] = None
    status: Optional[str] = None
    terms: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[PurchaseOrderItemCreate]] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    id: int
    po_number: str
    status: str
    subtotal: float
    discount: float
    tax_amount: float
    total: float
    created_at: datetime
    items: List[PurchaseOrderItemResponse] = []
    supplier: Optional[SupplierResponse] = None

    class Config:
        from_attributes = True


class GoodsReceivedItemBase(BaseModel):
    product_id: int
    ordered_quantity: float
    received_quantity: float
    accepted_quantity: float
    rejected_quantity: float = 0.0
    unit_price: float
    notes: Optional[str] = None


class GoodsReceivedItemCreate(GoodsReceivedItemBase):
    pass


class GoodsReceivedItemResponse(GoodsReceivedItemBase):
    id: int
    total: float

    class Config:
        from_attributes = True


class GoodsReceivedBase(BaseModel):
    purchase_order_id: int
    supplier_id: int
    received_date: date
    notes: Optional[str] = None


class GoodsReceivedCreate(GoodsReceivedBase):
    items: List[GoodsReceivedItemCreate]


class GoodsReceivedUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class GoodsReceivedResponse(GoodsReceivedBase):
    id: int
    grn_number: str
    status: str
    created_at: datetime
    items: List[GoodsReceivedItemResponse] = []

    class Config:
        from_attributes = True
