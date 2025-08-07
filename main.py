# backend_produits/main.py

from fastapi import FastAPI, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# These imports are now correct because 'backend_produits' is treated as a package
from . import crud as crud
from . import models as models
from . import schemas as schemas
from backend_produits.database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Application de gestion des produits")

# Add CORS middleware BEFORE defining routes
app.add_middleware( 
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",               # Pour le développement local React
        "http://127.0.0.1:3000",              # Alternative localhost
        "https://d8fa0eab8719.ngrok-free.app" # Si votre React est aussi sur ngrok (optionnel)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Bienvenue dans l'application de gestion des produits!"}

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/products/", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    return crud.create_product(db=db, product=product)

@app.get("/products/", response_model=List[schemas.Product])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = crud.get_products(db, skip=skip, limit=limit)
    return products

@app.get("/products/{product_id}", response_model=schemas.Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    db_product = crud.get_product(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@app.put("/products/{product_id}", response_model=schemas.Product)
def update_product(product_id: int, product: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = crud.update_product(db, product_id=product_id, product=product)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    success = crud.delete_product(db, product_id=product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return JSONResponse(content={"message": "Product deleted"})