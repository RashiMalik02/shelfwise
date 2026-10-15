from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..metrics import STOCK_MOVEMENTS
from ..models import Product, StockMovement
from ..schemas import MovementOut, ProductCreate, ProductOut, ProductUpdate, StockAdjustment

router = APIRouter(prefix="/api/products", tags=["products"])


def movement_out(movement: StockMovement) -> MovementOut:
    return MovementOut(
        id=movement.id,
        product_id=movement.product_id,
        sku=movement.product.sku,
        product_name=movement.product.name,
        delta=movement.delta,
        reason=movement.reason,
        note=movement.note,
        quantity_after=movement.quantity_after,
        created_at=movement.created_at,
    )


def record_movement(db: Session, product: Product, delta: int, reason: str, note: str = "") -> StockMovement:
    movement = StockMovement(
        product=product, delta=delta, reason=reason, note=note, quantity_after=product.quantity
    )
    db.add(movement)
    STOCK_MOVEMENTS.labels(reason=reason).inc()
    return movement


def get_product_or_404(db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return product


@router.get("", response_model=list[ProductOut])
def list_products(
    q: str | None = Query(default=None, max_length=80, description="Search SKU, name or supplier"),
    category: str | None = None,
    stock: Literal["OK", "LOW", "OUT"] | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    query = select(Product).order_by(Product.category, Product.name)
    if q:
        like = f"%{q.strip()}%"
        query = query.where(or_(Product.sku.ilike(like), Product.name.ilike(like), Product.supplier.ilike(like)))
    if category:
        query = query.where(Product.category == category)
    if stock == "OUT":
        query = query.where(Product.quantity == 0)
    elif stock == "LOW":
        query = query.where(Product.quantity > 0, Product.quantity <= Product.reorder_level)
    elif stock == "OK":
        query = query.where(Product.quantity > Product.reorder_level)
    return db.scalars(query).all()


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return get_product_or_404(db, product_id)


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**payload.model_dump())
    db.add(product)
    if product.quantity > 0:
        record_movement(db, product, product.quantity, "RECEIVED", "Opening stock")
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"SKU {payload.sku} already exists") from None
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = get_product_or_404(db, product_id)
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)

    new_quantity = changes.pop("quantity", None)
    for field, value in changes.items():
        setattr(product, field, value)

    if new_quantity is not None and new_quantity != product.quantity:
        delta = new_quantity - product.quantity
        product.quantity = new_quantity
        record_movement(db, product, delta, "COUNT", "Quantity corrected via edit")

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = get_product_or_404(db, product_id)
    db.delete(product)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{product_id}/adjust", response_model=ProductOut)
def adjust_stock(product_id: int, payload: StockAdjustment, db: Session = Depends(get_db)):
    product = get_product_or_404(db, product_id)
    if product.quantity + payload.delta < 0:
        raise HTTPException(
            status_code=409,
            detail=f"Only {product.quantity} units of {product.sku} on hand, cannot remove {-payload.delta}",
        )
    product.quantity += payload.delta
    record_movement(db, product, payload.delta, payload.reason, payload.note)
    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}/movements", response_model=list[MovementOut])
def product_movements(product_id: int, limit: int = Query(default=25, ge=1, le=200), db: Session = Depends(get_db)):
    get_product_or_404(db, product_id)
    rows = db.scalars(
        select(StockMovement)
        .options(selectinload(StockMovement.product))
        .where(StockMovement.product_id == product_id)
        .order_by(StockMovement.created_at.desc(), StockMovement.id.desc())
        .limit(limit)
    )
    return [movement_out(m) for m in rows]
