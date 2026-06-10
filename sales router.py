from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import random
import string

from app.database import get_db
from app.models.sales import Customer, Quotation, QuotationItem, Invoice, InvoiceItem, Payment
from app.schemas.sales import (
    CustomerCreate, CustomerUpdate, CustomerResponse,
    QuotationCreate, QuotationUpdate, QuotationResponse,
    InvoiceCreate, InvoiceUpdate, InvoiceResponse,
    PaymentCreate, PaymentResponse,
)
from app.core.security import require_any_role, require_manager_or_admin

router = APIRouter(prefix="/api/sales", tags=["Sales"])


def gen_code(prefix: str, length: int = 6) -> str:
    return f"{prefix}-{date.today().strftime('%Y%m')}-{''.join(random.choices(string.digits, k=length))}"


def calc_items(items_data):
    subtotal = discount = tax_amount = 0.0
    for item in items_data:
        line = item.quantity * item.unit_price
        disc = line * (item.discount / 100)
        taxable = line - disc
        tax = taxable * (item.tax_rate / 100)
        item_total = taxable + tax
        subtotal += line
        discount += disc
        tax_amount += tax
    total = subtotal - discount + tax_amount
    return subtotal, discount, tax_amount, total


# Customers
@router.get("/customers", response_model=List[CustomerResponse])
async def list_customers(
    skip: int = 0, limit: int = 100, search: Optional[str] = None,
    db: Session = Depends(get_db), current_user=Depends(require_any_role),
):
    query = db.query(Customer)
    if search:
        query = query.filter(
            (Customer.name.ilike(f"%{search}%")) |
            (Customer.email.ilike(f"%{search}%")) |
            (Customer.phone.ilike(f"%{search}%"))
        )
    return query.offset(skip).limit(limit).all()


@router.post("/customers", response_model=CustomerResponse, status_code=201)
async def create_customer(
    customer_in: CustomerCreate, db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    code = gen_code("CUST", 4)
    customer = Customer(**customer_in.model_dump(), customer_code=code)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int, db: Session = Depends(get_db), current_user=Depends(require_any_role)):
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")
    return c


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int, customer_update: CustomerUpdate,
    db: Session = Depends(get_db), current_user=Depends(require_manager_or_admin),
):
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")
    for f, v in customer_update.model_dump(exclude_unset=True).items():
        setattr(c, f, v)
    db.commit()
    db.refresh(c)
    return c


@router.delete("/customers/{customer_id}")
async def delete_customer(
    customer_id: int, db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")
    db.delete(c)
    db.commit()
    return {"message": "Customer deleted"}


# Quotations
@router.get("/quotations", response_model=List[QuotationResponse])
async def list_quotations(
    skip: int = 0, limit: int = 100, status: Optional[str] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db), current_user=Depends(require_any_role),
):
    query = db.query(Quotation)
    if status:
        query = query.filter(Quotation.status == status)
    if customer_id:
        query = query.filter(Quotation.customer_id == customer_id)
    return query.order_by(Quotation.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/quotations", response_model=QuotationResponse, status_code=201)
async def create_quotation(
    q_in: QuotationCreate, db: Session = Depends(get_db),
    current_user=Depends(require_any_role),
):
    subtotal, discount, tax_amount, total = calc_items(q_in.items)
    q_num = gen_code("QUO")
    while db.query(Quotation).filter(Quotation.quotation_number == q_num).first():
        q_num = gen_code("QUO")

    quotation = Quotation(
        quotation_number=q_num,
        customer_id=q_in.customer_id,
        date=q_in.date,
        valid_until=q_in.valid_until,
        terms=q_in.terms,
        notes=q_in.notes,
        subtotal=subtotal,
        discount=discount,
        tax_amount=tax_amount,
        total=total,
        created_by=current_user.id,
    )
    db.add(quotation)
    db.flush()

    for item_data in q_in.items:
        line = item_data.quantity * item_data.unit_price
        disc = line * (item_data.discount / 100)
        taxable = line - disc
        tax = taxable * (item_data.tax_rate / 100)
        item = QuotationItem(
            quotation_id=quotation.id,
            product_id=item_data.product_id,
            description=item_data.description,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            discount=item_data.discount,
            tax_rate=item_data.tax_rate,
            tax_amount=tax,
            total=taxable + tax,
        )
        db.add(item)

    db.commit()
    db.refresh(quotation)
    return quotation


@router.get("/quotations/{quotation_id}", response_model=QuotationResponse)
async def get_quotation(quotation_id: int, db: Session = Depends(get_db), current_user=Depends(require_any_role)):
    q = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return q


@router.put("/quotations/{quotation_id}", response_model=QuotationResponse)
async def update_quotation(
    quotation_id: int, q_update: QuotationUpdate,
    db: Session = Depends(get_db), current_user=Depends(require_any_role),
):
    q = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Quotation not found")
    for f, v in q_update.model_dump(exclude_unset=True, exclude={"items"}).items():
        setattr(q, f, v)
    if q_update.items is not None:
        for old_item in q.items:
            db.delete(old_item)
        subtotal, discount, tax_amount, total = calc_items(q_update.items)
        q.subtotal, q.discount, q.tax_amount, q.total = subtotal, discount, tax_amount, total
        for item_data in q_update.items:
            line = item_data.quantity * item_data.unit_price
            disc = line * (item_data.discount / 100)
            taxable = line - disc
            tax = taxable * (item_data.tax_rate / 100)
            item = QuotationItem(
                quotation_id=q.id, product_id=item_data.product_id,
                description=item_data.description, quantity=item_data.quantity,
                unit_price=item_data.unit_price, discount=item_data.discount,
                tax_rate=item_data.tax_rate, tax_amount=tax, total=taxable + tax,
            )
            db.add(item)
    db.commit()
    db.refresh(q)
    return q


@router.delete("/quotations/{quotation_id}")
async def delete_quotation(
    quotation_id: int, db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    q = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Quotation not found")
    db.delete(q)
    db.commit()
    return {"message": "Quotation deleted"}


# Invoices
@router.get("/invoices", response_model=List[InvoiceResponse])
async def list_invoices(
    skip: int = 0, limit: int = 100, status: Optional[str] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db), current_user=Depends(require_any_role),
):
    query = db.query(Invoice)
    if status:
        query = query.filter(Invoice.status == status)
    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)
    return query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/invoices", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    inv_in: InvoiceCreate, db: Session = Depends(get_db),
    current_user=Depends(require_any_role),
):
    subtotal, discount, tax_amount, total = calc_items(inv_in.items)
    inv_num = gen_code("INV")
    while db.query(Invoice).filter(Invoice.invoice_number == inv_num).first():
        inv_num = gen_code("INV")

    invoice = Invoice(
        invoice_number=inv_num,
        customer_id=inv_in.customer_id,
        quotation_id=inv_in.quotation_id,
        date=inv_in.date,
        due_date=inv_in.due_date,
        terms=inv_in.terms,
        notes=inv_in.notes,
        subtotal=subtotal,
        discount=discount,
        tax_amount=tax_amount,
        total=total,
        balance_due=total,
        created_by=current_user.id,
    )
    db.add(invoice)
    db.flush()

    for item_data in inv_in.items:
        line = item_data.quantity * item_data.unit_price
        disc = line * (item_data.discount / 100)
        taxable = line - disc
        tax = taxable * (item_data.tax_rate / 100)
        item = InvoiceItem(
            invoice_id=invoice.id, product_id=item_data.product_id,
            description=item_data.description, quantity=item_data.quantity,
            unit_price=item_data.unit_price, discount=item_data.discount,
            tax_rate=item_data.tax_rate, tax_amount=tax, total=taxable + tax,
        )
        db.add(item)

    db.commit()
    db.refresh(invoice)
    return invoice


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: int, db: Session = Depends(get_db), current_user=Depends(require_any_role)):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return inv


@router.put("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: int, inv_update: InvoiceUpdate,
    db: Session = Depends(get_db), current_user=Depends(require_any_role),
):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    for f, v in inv_update.model_dump(exclude_unset=True, exclude={"items"}).items():
        setattr(inv, f, v)
    if inv_update.items is not None:
        for old_item in inv.items:
            db.delete(old_item)
        subtotal, discount, tax_amount, total = calc_items(inv_update.items)
        inv.subtotal, inv.discount, inv.tax_amount, inv.total = subtotal, discount, tax_amount, total
        inv.balance_due = total - inv.paid_amount
        for item_data in inv_update.items:
            line = item_data.quantity * item_data.unit_price
            disc = line * (item_data.discount / 100)
            taxable = line - disc
            tax = taxable * (item_data.tax_rate / 100)
            item = InvoiceItem(
                invoice_id=inv.id, product_id=item_data.product_id,
                description=item_data.description, quantity=item_data.quantity,
                unit_price=item_data.unit_price, discount=item_data.discount,
                tax_rate=item_data.tax_rate, tax_amount=tax, total=taxable + tax,
            )
            db.add(item)
    db.commit()
    db.refresh(inv)
    return inv


@router.delete("/invoices/{invoice_id}")
async def delete_invoice(
    invoice_id: int, db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    db.delete(inv)
    db.commit()
    return {"message": "Invoice deleted"}


# Payments
@router.get("/payments", response_model=List[PaymentResponse])
async def list_payments(
    skip: int = 0, limit: int = 100,
    db: Session = Depends(get_db), current_user=Depends(require_any_role),
):
    return db.query(Payment).order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/payments", response_model=PaymentResponse, status_code=201)
async def create_payment(
    payment_in: PaymentCreate, db: Session = Depends(get_db),
    current_user=Depends(require_any_role),
):
    invoice = db.query(Invoice).filter(Invoice.id == payment_in.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if payment_in.amount > invoice.balance_due:
        raise HTTPException(status_code=400, detail="Payment exceeds balance due")

    pay_num = gen_code("PAY")
    while db.query(Payment).filter(Payment.payment_number == pay_num).first():
        pay_num = gen_code("PAY")

    payment = Payment(**payment_in.model_dump(), payment_number=pay_num, created_by=current_user.id)
    db.add(payment)

    invoice.paid_amount += payment_in.amount
    invoice.balance_due -= payment_in.amount
    if invoice.balance_due <= 0:
        invoice.status = "paid"
        invoice.balance_due = 0
    elif invoice.paid_amount > 0:
        invoice.status = "partial"

    db.commit()
    db.refresh(payment)
    return payment
