from pydantic import BaseModel
from datetime import datetime
from typing import List

class ProductIn(BaseModel):
    name: str
    stock: int
    price: float

class ProductOut(ProductIn):
    id: int

    class Config:
        orm_mode = True

class PurchaseIn(BaseModel):
    product_id: int
    quantity: int

class PurchaseOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    date: datetime

    class Config:
        orm_mode = True
