"""Loads a small demo catalogue so the dashboard isn't empty on first run.

Usage: python -m app.seed   (does nothing if products already exist)
"""

from decimal import Decimal

from sqlalchemy import func, select

from .database import SessionLocal
from .models import Product, StockMovement

DEMO_PRODUCTS = [
    # sku, name, category, qty, reorder, price, location, supplier
    ("PKG-1001", "Corrugated box 30x20x15", "Packaging", 420, 150, "0.85", "A-01", "Northline Packaging"),
    ("PKG-1002", "Bubble wrap roll 50m", "Packaging", 18, 25, "14.50", "A-02", "Northline Packaging"),
    ("PKG-1003", "Packing tape 48mm", "Packaging", 260, 80, "1.20", "A-02", "Northline Packaging"),
    ("ELC-2001", "USB-C cable 1m", "Electronics", 96, 40, "4.75", "B-04", "Voltway Traders"),
    ("ELC-2002", "Wireless barcode scanner", "Electronics", 6, 5, "48.00", "B-05", "Voltway Traders"),
    ("ELC-2003", "Thermal label printer", "Electronics", 0, 2, "129.00", "B-05", "Voltway Traders"),
    ("OFF-3001", "A4 copier paper (ream)", "Office", 75, 30, "4.10", "C-01", "Papyrus & Co"),
    ("OFF-3002", "Gel pen, blue (box of 12)", "Office", 12, 15, "3.60", "C-02", "Papyrus & Co"),
    ("OFF-3003", "Shipping labels 100x150 (500)", "Office", 34, 20, "9.90", "C-02", "Papyrus & Co"),
    ("SAF-4001", "Nitrile gloves, L (100)", "Safety", 140, 60, "6.40", "D-01", "Guardline Safety"),
    ("SAF-4002", "Hi-vis vest", "Safety", 9, 12, "5.25", "D-02", "Guardline Safety"),
    ("SAF-4003", "Steel-toe boots, size 9", "Safety", 0, 4, "42.00", "D-03", "Guardline Safety"),
    ("CLN-5001", "Floor cleaner 5L", "Cleaning", 22, 10, "11.30", "E-01", "Brightway Supplies"),
    ("CLN-5002", "Microfibre cloth (pack of 10)", "Cleaning", 48, 20, "7.80", "E-01", "Brightway Supplies"),
]


def seed() -> int:
    with SessionLocal() as db:
        if db.scalar(select(func.count(Product.id))):
            return 0
        for sku, name, category, qty, reorder, price, location, supplier in DEMO_PRODUCTS:
            product = Product(
                sku=sku,
                name=name,
                category=category,
                quantity=qty,
                reorder_level=reorder,
                unit_price=Decimal(price),
                location=location,
                supplier=supplier,
            )
            db.add(product)
            if qty:
                db.add(StockMovement(product=product, delta=qty, reason="RECEIVED", note="Opening stock", quantity_after=qty))
        db.commit()
        return len(DEMO_PRODUCTS)


if __name__ == "__main__":
    print(f"seeded {seed()} products")
