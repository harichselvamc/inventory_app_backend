from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import models, schemas
from typing import List, Optional

# --- Product CRUD Operations ---

def get_product(db: Session, product_id: int) -> Optional[models.Product]:
    """Fetches a single product by its ID."""
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def get_product_by_name(db: Session, name: str) -> Optional[models.Product]:
    """Fetches a single product by its name (case-insensitive)."""
    return db.query(models.Product).filter(func.lower(models.Product.name) == func.lower(name)).first()

def get_products(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[models.Product]:
    """
    Fetches a list of products with optional pagination and search.
    Search is performed case-insensitively on the product name.
    """
    query = db.query(models.Product)
    if search:
        query = query.filter(models.Product.name.ilike(f"%{search}%"))
    return query.order_by(models.Product.id).offset(skip).limit(limit).all()

def create_product(db: Session, product: schemas.ProductCreate) -> models.Product:
    """Creates a new product record in the database."""
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, product_update: schemas.ProductUpdate) -> Optional[models.Product]:
    """Updates an existing product's details."""
    db_product = get_product(db, product_id)
    if not db_product:
        return None
    
    update_data = product_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
        
    db.commit()
    db.refresh(db_product)
    return db_product

def delete_product(db: Session, product_id: int) -> Optional[models.Product]:
    """Deletes a product from the database."""
    db_product = get_product(db, product_id)
    if not db_product:
        return None
    db.delete(db_product)
    db.commit()
    return db_product

# --- Purchase & Reporting CRUD Operations ---

def record_bulk_purchase(db: Session, items: List[schemas.BulkPurchaseItem]) -> List[models.Purchase]:
    """
    Records a bulk purchase transaction.
    This function assumes stock validation has already happened.
    """
    purchases = [models.Purchase(**item.model_dump()) for item in items]
    db.add_all(purchases)
    # The commit is handled by the endpoint's transaction management
    return purchases

def get_sales_history(db: Session, skip: int = 0, limit: int = 100) -> List[models.Purchase]:
    """Fetches a list of all historical purchase records, most recent first."""
    return db.query(models.Purchase).order_by(desc(models.Purchase.date)).offset(skip).limit(limit).all()
