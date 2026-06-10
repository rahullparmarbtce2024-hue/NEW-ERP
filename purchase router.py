from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import random
import string

from app.database import get_db
from app.models.purchase import Supplier, PurchaseOrder, PurchaseOrderItem, GoodsReceived, GoodsReceivedItem
from app.models.inventory import Product, StockMovement
from app.schemas.purchase import (
    SupplierCreate, SupplierUpdate, SupplierResponse,
    PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderResponse,
    GoodsReceivedCreate, GoodsReceivedUpdate, GoodsReceivedResponse,
)
from app.core.security import require_any_role, require_manager_or_admin

router = APIRouter(prefix="/api/purchases", tags=["Purchases"])


def gen_code(prefix: str) -> str:
    return f"{prefix}-{date.today().strftime('%Y%m')}-{''.join(random.choices(string.digits, k=6))}"


# Suppliers
@router.get("/suppliers", response_model=List[SupplierResponse])
async def list_suppliers(
    skip: int = 0, limit: int = 100, search: Optional[str] = None,
    db: Session = Depends(get_db), current_user=Depends(require_any_role),
):
    query = db.query(Supplier)
    if search:
        query = query.filter(
            (Supplier.name.ilike(f"%{search}%")) |
            (Supplier.email.ilike(f"%{search}%"))
        )
    return query.offset(skip).limit(limit).all()


@router.post("/suppliers", response_model=SupplierResponse, status_code=201)
async def create_supplier(
    supplier_in: SupplierCreate, db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    code = gen_code("SUP")
    supplier = Supplier(**supplier_in.model_dump(), supplier_code=code)
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(supplier_id: int, db: Session = Depends(get_db), current_user=Depends(require_any_role)):
    s = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return s


@router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: int, supplier_update: SupplierUpdate,
    db: Session = Depends(get_db), current_user=Depends(require_manager_or_admin),
):
    s = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")
    for f, v in supplier_update.model_dump(exclude_unset=True).items():
        setattr(s, f, v)
    db.commit()
    db.refresh(s)
    return s


@router.delete("/suppliers/{supplier_id}")
async def delete_supplier(
    supplier_id: int, db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    s = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")
    db.delete(s)
    db.commit()
    return {"message": "Supplier deleted"}


# Purchase Orders
@router.get("/orders", response_model=List[PurchaseOrderResponse])
async def list_purchase_orders(
    skip: int = 0, limit: int = 100, status: Optional[str] = None,
    supplier_id: Optional[int] = None,
    db: Session = Depends(get_db), current_user=Depends(require_any_role),
):
    query = db.query(PurchaseOrder)
    if status:
        query = query.filter(PurchaseOrder.status == status)
    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)
    return query.order_by(PurchaseOrder.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/orders", response_model=PurchaseOrderResponse, status_code=201)
async def create_purchase_order(
    po_in: PurchaseOrderCreate, db: Session = Depends(get_db),
    current_user=Depends(require_any_role),
):
    subtotal = tax_amount = 0.0
    for item in po_in.items:
        line = item.quantity * item.unit_price
        tax = line * (item.tax_rate / 100)
        subtotal += line
        tax_amount += tax
    total = subtotal + tax_amount

    po_num = gen_code("PO")
    while db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_num).first():
        po_num = gen_code("PO")

    po = PurchaseOrder(
        po_number=po_num,
        supplier_id=po_in.supplier_id,
        date=po_in.date,
        expected_delivery=po_in.expected_delivery,
        terms=po_in.terms,
        notes=po_in.notes,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total=total,
        created_by=current_user.id,
    )
    db.add(po)
    db.flush()

    for item_data in po_in.items:
        line = item_data.quantity * item_data.unit_price
        tax = line * (item_data.tax_rate / 100)
        item = PurchaseOrderItem(
            purchase_order_id=po.id,
            product_id=item_data.product_id,
            description=item_data.description,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            tax_rate=item_data.tax_rate,
            tax_amount=tax,
            total=line + tax,
        )
        db.add(item)

    db.commit()
    db.refresh(po)
    return po


@router.get("/orders/{po_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(po_id: int, db: Session = Depends(get_db), current_user=Depends(require_any_role)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po


@router.put("/orders/{po_id}", response_model=PurchaseOrderResponse)
async def update_purchase_order(
    po_id: int, po_update: PurchaseOrderUpdate,
    db: Session = Depends(get_db), current_user=Depends(require_any_role),
):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    for f, v in po_update.model_dump(exclude_unset=True, exclude={"items"}).items():
        setattr(po, f, v)
    if po_update.items is not None:
        for old in po.items:
            db.delete(old)
        subtotal = tax_amount = 0.0
        for item_data in po_update.items:
            line = item_data.quantity * item_data.unit_price
            tax = line * (item_data.tax_rate / 100)
            subtotal += line
            tax_amount += tax
            item = PurchaseOrderItem(
                purchase_order_id=po.id,
                product_id=item_data.product_id,
                description=item_data.description,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                tax_rate=item_data.tax_rate,
                tax_amount=tax,
                total=line + tax,
            )
            db.add(item)
        po.subtotal, po.tax_amount, po.total = subtotal, tax_amount, subtotal + tax_amount
    db.commit()
    db.refresh(po)
    return po


@router.delete("/orders/{po_id}")
async def delete_purchase_order(
    po_id: int, db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    db.delete(po)
    db.commit()
    return {"message": "Purchase order deleted"}


# Goods Received
@router.get("/grn", response_model=List[GoodsReceivedResponse])
async def list_grn(
    skip: int = 0, limit: int = 100,
    db: Session = Depends(get_db), current_user=Depends(require_any_role),
):
    return db.query(GoodsReceived).order_by(GoodsReceived.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/grn", response_model=GoodsReceivedResponse, status_code=201)
async def create_grn(
    grn_in: GoodsReceivedCreate, db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    grn_num = gen_code("GRN")
    while db.query(GoodsReceived).filter(GoodsReceived.grn_number == grn_num).first():
        grn_num = gen_code("GRN")

    grn = GoodsReceived(
        grn_number=grn_num,
        purchase_order_id=grn_in.purchase_order_id,
        supplier_id=grn_in.supplier_id,
        received_date=grn_in.received_date,
        notes=grn_in.notes,
        created_by=current_user.id,
    )
    db.add(grn)
    db.flush()

    for item_data in grn_in.items:
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item_data.product_id} not found")

        total = item_data.accepted_quantity * item_data.unit_price
        item = GoodsReceivedItem(
            goods_received_id=grn.id,
            product_id=item_data.product_id,
            ordered_quantity=item_data.ordered_quantity,
            received_quantity=item_data.received_quantity,
            accepted_quantity=item_data.accepted_quantity,
            rejected_quantity=item_data.rejected_quantity,
            unit_price=item_data.unit_price,
            total=total,
            notes=item_data.notes,
        )
        db.add(item)

        # Update stock
        stock_before = product.current_stock
        product.current_stock += item_data.accepted_quantity
        movement = StockMovement(
            product_id=item_data.product_id,
            movement_type="in",
            quantity=item_data.accepted_quantity,
            unit_price=item_data.unit_price,
            total_price=total,
            reference_type="goods_received",
            reference_id=grn.id,
            stock_before=stock_before,
            stock_after=product.current_stock,
            notes=f"GRN: {grn_num}",
            created_by=current_user.id,
        )
        db.add(movement)

    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == grn_in.purchase_order_id).first()
    if po:
        po.status = "received"

    db.commit()
    db.refresh(grn)
    return grn


@router.get("/grn/{grn_id}", response_model=GoodsReceivedResponse)
async def get_grn(grn_id: int, db: Session = Depends(get_db), current_user=Depends(require_any_role)):
    grn = db.query(GoodsReceived).filter(GoodsReceived.id == grn_id).first()
    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")
    return grn
