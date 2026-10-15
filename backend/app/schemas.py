from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

StockStatus = Literal["OK", "LOW", "OUT"]
MovementReason = Literal["RECEIVED", "SOLD", "RETURNED", "DAMAGED", "COUNT"]

Price = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]
NonNegativeInt = Annotated[int, Field(ge=0, le=1_000_000)]


class ProductBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    category: str = Field(min_length=2, max_length=60)
    reorder_level: NonNegativeInt = 10
    unit_price: Price = Decimal("0.00")
    location: str = Field(default="", max_length=40)
    supplier: str = Field(default="", max_length=120)
    notes: str = Field(default="", max_length=2000)

    @field_validator("name", "category", "location", "supplier")
    @classmethod
    def strip(cls, value: str) -> str:
        return value.strip()


class ProductCreate(ProductBase):
    sku: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9-]+$")
    quantity: NonNegativeInt = 0

    @field_validator("sku")
    @classmethod
    def upper_sku(cls, value: str) -> str:
        return value.upper()


class ProductUpdate(BaseModel):
    """Partial update. Changing quantity here is treated as a stock count."""

    name: str | None = Field(default=None, min_length=2, max_length=160)
    category: str | None = Field(default=None, min_length=2, max_length=60)
    quantity: NonNegativeInt | None = None
    reorder_level: NonNegativeInt | None = None
    unit_price: Price | None = None
    location: str | None = Field(default=None, max_length=40)
    supplier: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=2000)


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    name: str
    category: str
    quantity: int
    reorder_level: int
    unit_price: float
    location: str
    supplier: str
    notes: str
    stock_status: StockStatus
    created_at: datetime
    updated_at: datetime


class StockAdjustment(BaseModel):
    delta: int = Field(ge=-100_000, le=100_000)
    reason: MovementReason
    note: str = Field(default="", max_length=240)

    @field_validator("delta")
    @classmethod
    def not_zero(cls, value: int) -> int:
        if value == 0:
            raise ValueError("delta must not be zero")
        return value


class MovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    sku: str
    product_name: str
    delta: int
    reason: str
    note: str
    quantity_after: int
    created_at: datetime


class CategorySummary(BaseModel):
    category: str
    skus: int
    units: int
    value: float


class InventoryStats(BaseModel):
    total_skus: int
    total_units: int
    inventory_value: float
    low_stock: int
    out_of_stock: int
    categories: list[CategorySummary]
