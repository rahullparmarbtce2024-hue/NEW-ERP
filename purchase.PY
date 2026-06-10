from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    supplier_code = Column(String(20), unique=True, index=True)
    name = Column(String(300), nullable=False)
    email = Column(String(255))
    phone = Column(String(20))
    company = Column(String(300))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    pincode = Column(String(10))
    gstin = Column(String(20))
    pan = Column(String(20))
    bank_account = Column(String(30))
    bank_name = Column(String(100))
    ifsc_code = Column(String(20))
    credit_terms = Column(Integer, default=30)  # days
    outstanding_balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(30), unique=True, nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    date = Column(Date, nullable=False)
    expected_delivery = Column(Date)
    status = Column(String(20), default="draft")  # draft, sent, partial, received, cancelled
    subtotal = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    terms = Column(Text)
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    supplier = relationship("Supplier", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
    goods_received = relationship("GoodsReceived", back_populates="purchase_order")


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"))
    description = Column(Text, nullable=False)
    quantity = Column(Float, nullable=False)
    received_quantity = Column(Float, default=0.0)
    unit_price = Column(Float, nullable=False)
    tax_rate = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    total = Column(Float, nullable=False)

    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product", back_populates="purchase_order_items")


class GoodsReceived(Base):
    __tablename__ = "goods_received"

    id = Column(Integer, primary_key=True, index=True)
    grn_number = Column(String(30), unique=True, nullable=False)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    received_date = Column(Date, nullable=False)
    status = Column(String(20), default="pending")  # pending, inspected, accepted, rejected
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    purchase_order = relationship("PurchaseOrder", back_populates="goods_received")
    items = relationship("GoodsReceivedItem", back_populates="goods_received", cascade="all, delete-orphan")


class GoodsReceivedItem(Base):
    __tablename__ = "goods_received_items"

    id = Column(Integer, primary_key=True, index=True)
    goods_received_id = Column(Integer, ForeignKey("goods_received.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    ordered_quantity = Column(Float, nullable=False)
    received_quantity = Column(Float, nullable=False)
    accepted_quantity = Column(Float, default=0.0)
    rejected_quantity = Column(Float, default=0.0)
    unit_price = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    notes = Column(Text)

    goods_received = relationship("GoodsReceived", back_populates="items")
