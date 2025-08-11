# backend_produits/schemas.py

from pydantic import BaseModel
from typing import Optional

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    image: Optional[str] = None  # URL de l'image

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    
    class Config:
        from_attributes = True  # Pour SQLAlchemy 2.0+
        # Si vous utilisez une version antérieure, utilisez:
        # orm_mode = True