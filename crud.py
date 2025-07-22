from sqlalchemy.orm import Session
from models import Product, Purchase
from schemas import ProductIn, PurchaseIn

def get_product(db: Session, product_id: int):
    return db.query(Product).filter(Product.id == product_id).first()

def get_product_by_name(db: Session, name: str):
    return db.query(Product).filter(Product.name == name).first()

def get_products(db: Session, skip: int = 0, limit: int = 20):
    return db.query(Product).offset(skip).limit(limit).all()

def create_product(db: Session, product: ProductIn):
    db_product = Product(name=product.name, stock=product.stock, price=product.price)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product_stock(db: Session, product_id: int, quantity: int):
    product = get_product(db, product_id)
    if product and product.stock >= quantity:
        product.stock -= quantity
        db.commit()
        return product
    return None

def create_purchase(db: Session, data: PurchaseIn):
    purchase = Purchase(product_id=data.product_id, quantity=data.quantity)
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    return purchase
