from fastapi import FastAPI, HTTPException
from models import Product, Purchase
from database import SessionLocal, init_db

app = FastAPI()
init_db()

@app.get("/products")
def get_products():
    db = SessionLocal()
    products = db.query(Product).all()
    return [{"id": p.id, "name": p.name, "stock": p.stock, "price": p.price} for p in products]

@app.post("/purchase")
def make_purchase(product_id: int, quantity: int):
    db = SessionLocal()
    product = db.query(Product).filter_by(id=product_id).first()

    if not product or product.stock < quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    product.stock -= quantity
    purchase = Purchase(product_id=product_id, quantity=quantity)
    db.add(purchase)
    db.commit()
    return {"message": "Purchase successful", "remaining_stock": product.stock}
