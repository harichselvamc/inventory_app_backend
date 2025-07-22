from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

# --- Product Schemas ---

class ProductBase(BaseModel):
    """Base schema for product, used for common fields."""
    name: str = Field(..., min_length=1, description="Name of the product")
    stock: int = Field(..., ge=0, description="Available stock quantity")
    price: float = Field(..., gt=0, description="Price of the product")

class ProductCreate(ProductBase):
    """Schema for creating a new product."""
    pass

class ProductUpdate(BaseModel):
    """Schema for updating an existing product. All fields are optional."""
    name: Optional[str] = Field(None, min_length=1)
    stock: Optional[int] = Field(None, ge=0)
    price: Optional[float] = Field(None, gt=0)

class ProductOut(ProductBase):
    """Schema for representing a product in API responses."""
    id: int

    class Config:
        from_attributes = True # Replaces orm_mode = True in Pydantic v2

# --- Purchase Schemas ---

class PurchaseBase(BaseModel):
    """Base schema for a single purchase item."""
    product_id: int
    quantity: int = Field(..., gt=0, description="Quantity must be positive")

class PurchaseCreate(PurchaseBase):
    """Schema for creating a single purchase record (used internally)."""
    pass

class PurchaseOut(PurchaseBase):
    """Schema for representing a purchase in API responses."""
    id: int
    date: datetime

    class Config:
        from_attributes = True

# --- Bulk Purchase Schemas ---

class BulkPurchaseItem(BaseModel):
    """Defines a single item within a bulk purchase request."""
    product_id: int
    quantity: int = Field(..., gt=0)

class BulkPurchaseRequest(BaseModel):
    """The request model for the bulk purchase endpoint."""
    items: List[BulkPurchaseItem]


# --- Reporting Schemas ---

class SaleReportItem(BaseModel):
    """Defines the structure for an item in the sales report."""
    product_name: str
    quantity: int
    total_price: float
    date: datetime

    class Config:
        from_attributes = True
