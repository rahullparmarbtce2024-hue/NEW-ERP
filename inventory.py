from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    unit: str = "pcs"
    purchase_price: float = 0.0
    selling_price: float = 0.0
    minimum_stock: float = 0.0
    maximum_stock: float = 0.0
    reorder_point: float = 0.0
    tax_rate: float = 0.0
    location: Optional[str] = None
    barcode: Optional[str] = None
    is_active: bool = True


class ProductCreate(ProductBase):
    sku: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    unit: Optional[str] = None
    purchase_price: Optional[float] = None
    selling_price: Optional[float] = None
    minimum_stock: Optional[float] = None
    maximum_stock: Optional[float] = None
    reorder_point: Optional[float] = None
    tax_rate: Optional[float] = None
    location: Optional[str] = None
    barcode: Optional[str] = None
    is_active: Optional[bool] = None
    image_url: Optional[str] = None


class ProductResponse(ProductBase):
    id: int
    sku: str
    current_stock: float
    image_url: Optional[str] = None
    created_at: datetime
    category: Optional[CategoryResponse] = None

    class Config:
        from_attributes = True


class StockMovementBase(BaseModel):
    product_id: int
    movement_type: str  # in or out
    quantity: float
    unit_price: float = 0.0
    notes: Optional[str] = None


class StockMovementCreate(StockMovementBase):
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None


class StockMovementResponse(StockMovementBase):
    id: int
    total_price: float
    stock_before: float
    stock_after: float
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    created_at: datetime
    product: Optional[ProductResponse] = None

    class Config:
        from_attributes = True
