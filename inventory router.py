from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import random
import string

from app.database import get_db
from app.models.inventory import Category, Product, StockMovement
from app.schemas.inventory import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    ProductCreate, ProductUpdate, ProductResponse,
    StockMovementCreate, StockMovementResponse,
)
from app.core.security import get_current_active_user, require_manager_or_admin, require_any_role

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


def generate_sku():
    return "SKU-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


# Categories
@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role),
):
    return db.query(Category).order_by(Category.name).all()


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    existing = db.query(Category).filter(Category.name == category_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    category = Category(**category_in.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    for field, value in category_update.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    db.commit()
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()
    return {"message": "Category deleted"}


# Products
@router.get("/products", response_model=List[ProductResponse])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    low_stock: Optional[bool] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role),
):
    query = db.query(Product)
    if search:
        query = query.filter(
            (Product.name.ilike(f"%{search}%")) |
            (Product.sku.ilike(f"%{search}%")) |
            (Product.barcode.ilike(f"%{search}%"))
        )
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if low_stock:
        query = query.filter(Product.current_stock <= Product.reorder_point)
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    return query.offset(skip).limit(limit).all()


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    sku = product_in.sku or generate_sku()
    while db.query(Product).filter(Product.sku == sku).first():
        sku = generate_sku()

    product = Product(**product_in.model_dump(exclude={"sku"}), sku=sku)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/products/low-stock", response_model=List[ProductResponse])
async def get_low_stock_products(
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role),
):
    return db.query(Product).filter(
        Product.current_stock <= Product.reorder_point,
        Product.is_active == True,
    ).all()


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in product_update.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted"}


# Stock Movements
@router.get("/stock-movements", response_model=List[StockMovementResponse])
async def list_stock_movements(
    skip: int = 0,
    limit: int = 100,
    product_id: Optional[int] = None,
    movement_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role),
):
    query = db.query(StockMovement)
    if product_id:
        query = query.filter(StockMovement.product_id == product_id)
    if movement_type:
        query = query.filter(StockMovement.movement_type == movement_type)
    return query.order_by(StockMovement.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/stock-movements", response_model=StockMovementResponse, status_code=status.HTTP_201_CREATED)
async def create_stock_movement(
    movement_in: StockMovementCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    product = db.query(Product).filter(Product.id == movement_in.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if movement_in.movement_type == "out" and product.current_stock < movement_in.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    stock_before = product.current_stock
    if movement_in.movement_type == "in":
        product.current_stock += movement_in.quantity
    else:
        product.current_stock -= movement_in.quantity

    movement = StockMovement(
        **movement_in.model_dump(),
        total_price=movement_in.quantity * movement_in.unit_price,
        stock_before=stock_before,
        stock_after=product.current_stock,
        created_by=current_user.id,
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement
