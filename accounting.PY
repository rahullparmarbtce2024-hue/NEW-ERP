from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class AccountCategory(Base):
    __tablename__ = "account_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    type = Column(String(20), nullable=False)  # income, expense, asset, liability
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    transactions = relationship("Transaction", back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_number = Column(String(30), unique=True, nullable=False)
    type = Column(String(20), nullable=False)  # income, expense
    category_id = Column(Integer, ForeignKey("account_categories.id"))
    date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    payment_method = Column(String(50))
    reference_number = Column(String(100))
    reference_type = Column(String(50))  # invoice, purchase_order, manual
    reference_id = Column(Integer)
    notes = Column(Text)
    attachment_url = Column(String(500))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    category = relationship("AccountCategory", back_populates="transactions")


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    account_name = Column(String(200), nullable=False)
    description = Column(Text)
    debit = Column(Float, default=0.0)
    credit = Column(Float, default=0.0)
    balance = Column(Float, default=0.0)
    reference_type = Column(String(50))
    reference_id = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
