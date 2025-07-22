from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

# Import the correct model and schema modules
import models
import schemas
import crud
from database import SessionLocal, engine

# Create all database tables on startup using the Base from models
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Inventory API",
    version="3.0",
    description="A robust API for managing inventory, sales, and reporting.",
)

# --- Dependency ---
def get_db():
    """Dependency to get a DB session for each request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- API Endpoints ---

@app.get("/health", tags=["System"])
def health_check():
    """A simple health check endpoint to confirm the API is running."""
    return {"status": "ok"}

# --- Product Management Endpoints ---

@app.post("/products", response_model=schemas.ProductOut, status_code=201, tags=["Products"])
def create_new_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    """Creates a new product in the inventory."""
    if crud.get_product_by_name(db, product.name):
        raise HTTPException(status_code=400, detail="Product with this name already exists.")
    return crud.create_product(db, product)

@app.get("/products", response_model=List[schemas.ProductOut], tags=["Products"])
def read_products(
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Retrieves a list of all products, with optional search and pagination."""
    return crud.get_products(db, skip=skip, limit=limit, search=search)

@app.get("/products/{product_id}", response_model=schemas.ProductOut, tags=["Products"])
def read_product(product_id: int, db: Session = Depends(get_db)):
    """Retrieves a single product by its ID."""
    db_product = crud.get_product(db, product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    return db_product

@app.put("/products/{product_id}", response_model=schemas.ProductOut, tags=["Products"])
def update_existing_product(product_id: int, product: schemas.ProductUpdate, db: Session = Depends(get_db)):
    """Updates the details of an existing product."""
    db_product = crud.update_product(db, product_id, product)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    return db_product

@app.delete("/products/{product_id}", status_code=204, tags=["Products"])
def delete_existing_product(product_id: int, db: Session = Depends(get_db)):
    """Deletes a product from the inventory."""
    db_product = crud.delete_product(db, product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    return # No content to return on successful deletion

# --- Sales & Purchase Endpoints ---

@app.post("/purchases/bulk", status_code=201, tags=["Sales"])
def make_bulk_purchase(request: schemas.BulkPurchaseRequest, db: Session = Depends(get_db)):
    """
    Processes a cart of items in a single, atomic transaction.
    Stock levels are checked for all items before any changes are made.
    """
    try:
        with db.begin_nested(): # Use a nested transaction for atomicity
            product_ids = [item.product_id for item in request.items]
            # CORRECTED LINE: Query the 'models.Product' table, not the schema
            products = db.query(models.Product).filter(models.Product.id.in_(product_ids)).all()
            product_map = {p.id: p for p in products}

            # --- Validation Step ---
            for item in request.items:
                product = product_map.get(item.product_id)
                if not product:
                    raise HTTPException(status_code=404, detail=f"Product with ID {item.product_id} not found.")
                if product.stock < item.quantity:
                    raise HTTPException(status_code=400, detail=f"Insufficient stock for '{product.name}'. Available: {product.stock}, Requested: {item.quantity}.")

            # --- Processing Step ---
            for item in request.items:
                product = product_map[item.product_id]
                product.stock -= item.quantity
            
            crud.record_bulk_purchase(db, request.items)
        
        # Only commit if the nested block succeeded
        db.commit()

    except Exception as e:
        db.rollback() # Rollback any changes if an error occurred
        logging.error(f"Bulk purchase failed: {e}")
        # Re-raise the original exception or a generic one
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="An internal error occurred during the transaction.")

    return {"message": "Purchase successful. Inventory updated."}


# --- Reporting Endpoints ---

@app.get("/reports/sales", response_model=List[schemas.SaleReportItem], tags=["Reports"])
def get_sales_report(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieves a historical report of all sales, including product details."""
    purchases = crud.get_sales_history(db, skip=skip, limit=limit)
    report = []
    for p in purchases:
        if p.product:
            report.append(schemas.SaleReportItem(
                product_name=p.product.name,
                quantity=p.quantity,
                total_price=p.product.price * p.quantity,
                date=p.date
            ))
    return report
