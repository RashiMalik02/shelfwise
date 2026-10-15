from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import Product, StockMovement
from ..schemas import CategorySummary, InventoryStats, MovementOut
from .products import movement_out

router = APIRouter(prefix="/api", tags=["insights"])


@router.get("/stats", response_model=InventoryStats)
def inventory_stats(db: Session = Depends(get_db)):
    value = func.coalesce(func.sum(Product.quantity * Product.unit_price), 0)
    totals = db.execute(
        select(
            func.count(Product.id),
            func.coalesce(func.sum(Product.quantity), 0),
            value,
            func.coalesce(func.sum(case((Product.quantity == 0, 1), else_=0)), 0),
            func.coalesce(
                func.sum(case(((Product.quantity > 0) & (Product.quantity <= Product.reorder_level), 1), else_=0)),
                0,
            ),
        )
    ).one()

    by_category = db.execute(
        select(Product.category, func.count(Product.id), func.sum(Product.quantity), value)
        .group_by(Product.category)
        .order_by(value.desc())
    ).all()

    return InventoryStats(
        total_skus=totals[0],
        total_units=totals[1],
        inventory_value=round(float(totals[2]), 2),
        out_of_stock=totals[3],
        low_stock=totals[4],
        categories=[
            CategorySummary(category=c, skus=n, units=u or 0, value=round(float(v or 0), 2))
            for c, n, u, v in by_category
        ],
    )


@router.get("/categories", response_model=list[str])
def categories(db: Session = Depends(get_db)):
    return db.scalars(select(Product.category).distinct().order_by(Product.category)).all()


@router.get("/movements", response_model=list[MovementOut])
def recent_movements(limit: int = Query(default=15, ge=1, le=200), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(StockMovement)
        .options(selectinload(StockMovement.product))
        .order_by(StockMovement.created_at.desc(), StockMovement.id.desc())
        .limit(limit)
    )
    return [movement_out(m) for m in rows]
