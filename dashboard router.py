from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import date, datetime, timedelta

from app.database import get_db
from app.models.user import User
from app.models.employee import Employee, Attendance
from app.models.inventory import Product
from app.models.sales import Invoice, Payment, Customer
from app.models.purchase import PurchaseOrder
from app.models.accounting import Transaction
from app.core.security import require_any_role, require_manager_or_admin

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/kpis")
async def get_kpis(
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role),
):
    today = date.today()
    first_of_month = today.replace(day=1)

    # Revenue this month
    revenue_month = db.query(func.sum(Payment.amount)).filter(
        Payment.payment_date >= first_of_month
    ).scalar() or 0.0

    # Revenue last month
    last_month_end = first_of_month - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    revenue_last_month = db.query(func.sum(Payment.amount)).filter(
        Payment.payment_date >= last_month_start,
        Payment.payment_date <= last_month_end,
    ).scalar() or 0.0

    # Total invoices
    total_invoices = db.query(Invoice).count()
    unpaid_invoices = db.query(Invoice).filter(Invoice.status.in_(["sent", "partial", "overdue"])).count()

    # Employees
    total_employees = db.query(Employee).filter(Employee.status == "active").count()

    # Present today
    present_today = db.query(Attendance).filter(
        Attendance.date == today,
        Attendance.status.in_(["present", "work_from_home", "half_day"]),
    ).count()

    # Total products / low stock
    total_products = db.query(Product).filter(Product.is_active == True).count()
    low_stock = db.query(Product).filter(
        Product.current_stock <= Product.reorder_point,
        Product.is_active == True,
    ).count()

    # Total customers
    total_customers = db.query(Customer).filter(Customer.is_active == True).count()

    # Expenses this month
    expenses_month = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == "expense",
        extract("month", Transaction.date) == today.month,
        extract("year", Transaction.date) == today.year,
    ).scalar() or 0.0

    # Pending POs
    pending_pos = db.query(PurchaseOrder).filter(PurchaseOrder.status.in_(["draft", "sent"])).count()

    # Revenue trend (last 6 months)
    revenue_trend = []
    for i in range(5, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        rev = db.query(func.sum(Payment.amount)).filter(
            extract("month", Payment.payment_date) == m,
            extract("year", Payment.payment_date) == y,
        ).scalar() or 0.0
        revenue_trend.append({
            "month": f"{y}-{m:02d}",
            "revenue": round(float(rev), 2),
        })

    revenue_change = 0.0
    if revenue_last_month > 0:
        revenue_change = ((revenue_month - revenue_last_month) / revenue_last_month) * 100

    return {
        "revenue": {
            "current_month": round(float(revenue_month), 2),
            "last_month": round(float(revenue_last_month), 2),
            "change_percent": round(revenue_change, 1),
        },
        "invoices": {
            "total": total_invoices,
            "unpaid": unpaid_invoices,
        },
        "employees": {
            "total": total_employees,
            "present_today": present_today,
            "attendance_rate": round((present_today / total_employees * 100) if total_employees > 0 else 0, 1),
        },
        "inventory": {
            "total_products": total_products,
            "low_stock_count": low_stock,
        },
        "customers": {
            "total": total_customers,
        },
        "expenses": {
            "current_month": round(float(expenses_month), 2),
        },
        "purchase_orders": {
            "pending": pending_pos,
        },
        "revenue_trend": revenue_trend,
    }


@router.get("/recent-activity")
async def get_recent_activity(
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role),
):
    # Recent invoices
    recent_invoices = db.query(Invoice).order_by(Invoice.created_at.desc()).limit(5).all()
    # Recent payments
    recent_payments = db.query(Payment).order_by(Payment.created_at.desc()).limit(5).all()
    # Recent POs
    recent_pos = db.query(PurchaseOrder).order_by(PurchaseOrder.created_at.desc()).limit(5).all()

    return {
        "recent_invoices": [
            {
                "id": inv.id,
                "number": inv.invoice_number,
                "customer_id": inv.customer_id,
                "total": inv.total,
                "status": inv.status,
                "date": str(inv.date),
            }
            for inv in recent_invoices
        ],
        "recent_payments": [
            {
                "id": p.id,
                "number": p.payment_number,
                "amount": p.amount,
                "date": str(p.payment_date),
            }
            for p in recent_payments
        ],
        "recent_purchase_orders": [
            {
                "id": po.id,
                "number": po.po_number,
                "supplier_id": po.supplier_id,
                "total": po.total,
                "status": po.status,
                "date": str(po.date),
            }
            for po in recent_pos
        ],
    }


@router.get("/inventory-stats")
async def get_inventory_stats(
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role),
):
    from app.models.inventory import Category

    # Products by category
    by_category = db.query(
        Category.name,
        func.count(Product.id).label("count"),
        func.sum(Product.current_stock * Product.selling_price).label("value"),
    ).join(Product, Product.category_id == Category.id).group_by(Category.name).all()

    low_stock_products = db.query(Product).filter(
        Product.current_stock <= Product.reorder_point,
        Product.is_active == True,
    ).limit(10).all()

    return {
        "by_category": [
            {
                "category": r.name,
                "count": r.count,
                "value": round(float(r.value or 0), 2),
            }
            for r in by_category
        ],
        "low_stock_alerts": [
            {
                "id": p.id,
                "sku": p.sku,
                "name": p.name,
                "current_stock": p.current_stock,
                "reorder_point": p.reorder_point,
                "unit": p.unit,
            }
            for p in low_stock_products
        ],
    }
