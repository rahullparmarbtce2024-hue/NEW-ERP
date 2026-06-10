from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(300), nullable=False)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey("categories.id"))
    unit = Column(String(50), default="pcs")
    purchase_price = Column(Float, default=0.0)
    selling_price = Column(Float, default=0.0)
    current_stock = Column(Float, default=0.0)
    minimum_stock = Column(Float, default=0.0)
    maximum_stock = Column(Float, default=0.0)
    reorder_point = Column(Float, default=0.0)
    image_url = Column(String(500))
    barcode = Column(String(100))
    is_active = Column(Boolean, default=True)
    tax_rate = Column(Float, default=0.0)
    location = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    category = relationship("Category", back_populates="products")
    stock_movements = relationship("StockMovement", back_populates="product")
    invoice_items = relationship("InvoiceItem", back_populates="product")
    purchase_order_items = relationship("PurchaseOrderItem", back_populates="product")


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    movement_type = Column(String(10), nullable=False)  # "in" or "out"
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, default=0.0)
    total_price = Column(Float, default=0.0)
    reference_type = Column(String(50))  # "purchase_order", "invoice", "adjustment"
    reference_id = Column(Integer)
    stock_before = Column(Float, default=0.0)
    stock_after = Column(Float, default=0.0)
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="stock_movements")
