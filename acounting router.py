from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Optional
from datetime import date
import random
import string

from app.database import get_db
from app.models.accounting import AccountCategory, Transaction, LedgerEntry
from app.schemas.accounting import (
    AccountCategoryCreate, AccountCategoryUpdate, AccountCategoryResponse,
    TransactionCreate, TransactionUpdate, TransactionResponse,
    LedgerEntryCreate, LedgerEntryResponse, FinancialSummary,
)
from app.core.security import require_any_role, require_manager_or_admin

router = APIRouter(prefix="/api/accounting", tags=["Accounting"])


def gen_txn_number() -> str:
    return f"TXN-{date.today().strftime('%Y%m')}-{''.join(random.choices(string.digits, k=6))}"


# Account Categories
@router.get("/categories", response_model=List[AccountCategoryResponse])
async def list_account_categories(
    type: Optional[str] = None,
    db: Session = Depends(get_db), current_user=Depends(require_any_role),
):
    query = db.query(AccountCategory)
    if type:
        query = query.filter(AccountCategory.type == type)
    return query.order_by(AccountCategory.name).all()


@router.post("/categories", response_model=AccountCategoryResponse, status_code=201)
async def create_account_category(
    cat_in: AccountCategoryCreate, db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    cat = AccountCategory(**cat_in.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.put("/categories/{cat_id}", response_model=AccountCategoryResponse)
async def update_account_category(
    cat_id: int, cat_update: AccountCategoryUpdate,
    db: Session = Depends(get_db), current_user=Depends(require_manager_or_admin),
):
    cat = db.query(AccountCategory).filter(AccountCategory.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    for f, v in cat_update.model_dump(exclude_unset=True).items():
        setattr(cat, f, v)
    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/categories/{cat_id}")
async def delete_account_category(
    cat_id: int, db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    cat = db.query(AccountCategory).filter(AccountCategory.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(cat)
    db.commit()
    return {"message": "Category deleted"}


# Transactions
@router.get("/transactions", response_model=List[TransactionResponse])
async def list_transactions(
    skip: int = 0, limit: int = 100,
    type: Optional[str] = None,
    category_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db), current_user=Depends(require_any_role),
):
    query = db.query(Transaction)
    if type:
        query = query.filter(Transaction.type == type)
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    return query.order_by(Transaction.date.desc()).offset(skip).limit(limit).all()


@router.post("/transactions", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    txn_in: TransactionCreate, db: Session = Depends(get_db),
    current_user=Depends(require_any_role),
):
    txn_num = gen_txn_number()
    while db.query(Transaction).filter(Transaction.transaction_number == txn_num).first():
        txn_num = gen_txn_number()

    transaction = Transaction(**txn_in.model_dump(), transaction_number=txn_num, created_by=current_user.id)
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("/transactions/{txn_id}", response_model=TransactionResponse)
async def get_transaction(txn_id: int, db: Session = Depends(get_db), current_user=Depends(require_any_role)):
    txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn


@router.put("/transactions/{txn_id}", response_model=TransactionResponse)
async def update_transaction(
    txn_id: int, txn_update: TransactionUpdate,
    db: Session = Depends(get_db), current_user=Depends(require_manager_or_admin),
):
    txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    for f, v in txn_update.model_dump(exclude_unset=True).items():
        setattr(txn, f, v)
    db.commit()
    db.refresh(txn)
    return txn


@router.delete("/transactions/{txn_id}")
async def delete_transaction(
    txn_id: int, db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(txn)
    db.commit()
    return {"message": "Transaction deleted"}


# Ledger
@router.get("/ledger", response_model=List[LedgerEntryResponse])
async def get_ledger(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    account_name: Optional[str] = None,
    db: Session = Depends(get_db), current_user=Depends(require_any_role),
):
    query = db.query(LedgerEntry)
    if start_date:
        query = query.filter(LedgerEntry.date >= start_date)
    if end_date:
        query = query.filter(LedgerEntry.date <= end_date)
    if account_name:
        query = query.filter(LedgerEntry.account_name.ilike(f"%{account_name}%"))
    return query.order_by(LedgerEntry.date.desc()).all()


@router.post("/ledger", response_model=LedgerEntryResponse, status_code=201)
async def create_ledger_entry(
    entry_in: LedgerEntryCreate, db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    entry = LedgerEntry(**entry_in.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


# Financial Reports
@router.get("/reports/summary")
async def get_financial_summary(
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    query = db.query(Transaction)
    if year:
        query = query.filter(extract("year", Transaction.date) == year)
    if month:
        query = query.filter(extract("month", Transaction.date) == month)

    income_total = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == "income",
        *(
            [extract("year", Transaction.date) == year] if year else []
        ),
        *(
            [extract("month", Transaction.date) == month] if month else []
        ),
    ).scalar() or 0.0

    expense_total = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == "expense",
        *(
            [extract("year", Transaction.date) == year] if year else []
        ),
        *(
            [extract("month", Transaction.date) == month] if month else []
        ),
    ).scalar() or 0.0

    # Monthly trend (last 12 months)
    monthly_data = db.query(
        extract("year", Transaction.date).label("year"),
        extract("month", Transaction.date).label("month"),
        Transaction.type,
        func.sum(Transaction.amount).label("total"),
    ).group_by(
        extract("year", Transaction.date),
        extract("month", Transaction.date),
        Transaction.type,
    ).order_by(
        extract("year", Transaction.date),
        extract("month", Transaction.date),
    ).limit(24).all()

    trend = {}
    for row in monthly_data:
        key = f"{int(row.year)}-{int(row.month):02d}"
        if key not in trend:
            trend[key] = {"period": key, "income": 0.0, "expense": 0.0}
        trend[key][row.type] = float(row.total)

    # By category
    income_by_cat = db.query(
        AccountCategory.name, func.sum(Transaction.amount).label("total")
    ).join(Transaction, Transaction.category_id == AccountCategory.id).filter(
        Transaction.type == "income"
    ).group_by(AccountCategory.name).all()

    expense_by_cat = db.query(
        AccountCategory.name, func.sum(Transaction.amount).label("total")
    ).join(Transaction, Transaction.category_id == AccountCategory.id).filter(
        Transaction.type == "expense"
    ).group_by(AccountCategory.name).all()

    return {
        "total_income": income_total,
        "total_expense": expense_total,
        "net_profit": income_total - expense_total,
        "income_by_category": [{"name": r.name, "total": float(r.total)} for r in income_by_cat],
        "expense_by_category": [{"name": r.name, "total": float(r.total)} for r in expense_by_cat],
        "monthly_trend": list(trend.values()),
    }
