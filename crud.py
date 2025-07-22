from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from models import Product, Purchase
from schemas import ProductCreate, ProductUpdate, BulkPurchaseItem
from typing import List, Optional

# --- Product CRUD Operations ---

def get_product(db: Session, product_id: int) -> Optional[Product]:
    """Fetches a single product by its ID."""
    return db.query(Product).filter(Product.id == product_id).first()

def get_product_by_name(db: Session, name: str) -> Optional[Product]:
    """Fetches a single product by its name (case-insensitive)."""
    return db.query(Product).filter(func.lower(Product.name) == func.lower(name)).first()

def get_products(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[Product]:
    """
    Fetches a list of products with optional pagination and search.
    Search is performed case-insensitively on the product name.
    """
    query = db.query(Product)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()

def create_product(db: Session, product: ProductCreate) -> Product:
    """Creates a new product record in the database."""
    db_product = Product(name=product.name, stock=product.stock, price=product.price)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, product_update: ProductUpdate) -> Optional[Product]:
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

def delete_product(db: Session, product_id: int) -> Optional[Product]:
    """Deletes a product from the database."""
    db_product = get_product(db, product_id)
    if not db_product:
        return None
    db.delete(db_product)
    db.commit()
    return db_product

# --- Purchase & Reporting CRUD Operations ---

def record_bulk_purchase(db: Session, items: List[BulkPurchaseItem]) -> List[Purchase]:
    """
    Records a bulk purchase transaction.
    This function assumes stock validation has already happened.
    """
    purchases = []
    for item in items:
        # This part just records the sale. Stock reduction is handled in the endpoint.
        purchase = Purchase(product_id=item.product_id, quantity=item.quantity)
        purchases.append(purchase)
    
    db.add_all(purchases)
    db.commit()
    return purchases

def get_sales_history(db: Session, skip: int = 0, limit: int = 100) -> List[Purchase]:
    """Fetches a list of all historical purchase records, most recent first."""
    return db.query(Purchase).order_by(desc(Purchase.date)).offset(skip).limit(limit).all()

