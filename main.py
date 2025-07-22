from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from crud import get_products_with_sno
from fastapi.responses import JSONResponse
from functools import lru_cache
import time
app = FastAPI(title="Inventory API", version="2.0")
init_db()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Health check (ping from GUI to keep alive)
@app.get("/health")
def health_check():
    return cached_health_status()
# In-memory cache with 10s expiration
product_cache = {"timestamp": 0, "data": []}
CACHE_TTL = 10

@app.get("/products")
def list_products(db: Session = Depends(get_db)):
    global product_cache
    now = time.time()
    if now - product_cache["timestamp"] > CACHE_TTL:
        product_cache["data"] = get_products_with_sno(db)
        product_cache["timestamp"] = now
    return JSONResponse(content=product_cache["data"])
# Product Endpoints
@app.get("/products", response_model=list[schemas.ProductOut])
def list_products(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return crud.get_products(db, skip=skip, limit=limit)

@app.post("/add_product", response_model=schemas.ProductOut)
def add_product(product: schemas.ProductIn, db: Session = Depends(get_db)):
    if crud.get_product_by_name(db, product.name):
        raise HTTPException(status_code=400, detail="Product already exists")
    return crud.create_product(db, product)

@app.get("/product/{product_id}", response_model=schemas.ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# Purchase Endpoint
@app.post("/purchase")
def make_purchase(data: schemas.PurchaseIn, db: Session = Depends(get_db)):
    product = crud.update_product_stock(db, data.product_id, data.quantity)
    if not product:
        raise HTTPException(status_code=400, detail="Insufficient stock or invalid product")
    purchase = crud.create_purchase(db, data)
    return {"message": "Purchase successful", "remaining_stock": product.stock}
