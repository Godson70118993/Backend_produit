# FastAPI Backend Fix Plan

## Issues Identified

1. **Relative Import Issues**: The error occurs because relative imports (with `.` prefix) are being used, but the backend_produits directory is not recognized as a proper Python package.
2. **Missing Imports**: The main.py file is missing imports for `Depends` and `List`.
3. **Database URL**: The database URL in database.py points to "test.db" but you have a "products.db" file.

## Solution Steps

### 1. Create an __init__.py file

Create an empty `__init__.py` file in the backend_produits directory to make it a proper Python package:

```python
# This file makes the backend_produits directory a Python package
```

### 2. Fix main.py

Here's the corrected version of main.py with all issues fixed:

```python
from fastapi import FastAPI, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
import crud, models, schemas
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

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


@app.put("/api/products/{product_id}", response_model=schemas.Product)
def update_product(product_id: int, product: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = crud.update_product(db, product_id=product_id, product=product)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    success = crud.delete_product(db, product_id=product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return JSONResponse(content={"message": "Product deleted"})
```

### 3. Fix models.py

Change the relative import in models.py:

```python
from sqlalchemy import Column, Integer, String, Float
from database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    price = Column(Float, index=True)
```

### 4. Fix crud.py

Change the relative import in crud.py:

```python
from sqlalchemy.orm import Session
import models, schemas


def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def get_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).offset(skip).limit(limit).all()


def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(name=product.name, description=product.description, price=product.price)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, product: schemas.ProductCreate):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if db_product:
        db_product.name = product.name
        db_product.description = product.description
        db_product.price = product.price
        db.commit()
        db.refresh(db_product)
    return db_product

def delete_product(db: Session, product_id: int):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if db_product:
        db.delete(db_product)
        db.commit()
        return True
    return False
```

### 5. Fix database.py

Update the database URL to point to products.db:

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./products.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
```

## Running the Application

After making these changes, you should be able to run the application with:

```bash
cd /home/godsonpatam/Documents/Fullstack_Blog_produits
uvicorn backend_produits.main:app --reload
```

This command tells uvicorn to look for the app object inside the backend_produits.main module, which should work now that we've made backend_produits a proper package with an __init__.py file.