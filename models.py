# backend_produits/models.py

from sqlalchemy import Column, Integer, String, Float
from .database import Base # Use relative import for database as well

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    price = Column(Float)