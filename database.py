# backend_produits/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# URL de connexion (SQLite par défaut)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

# Paramètres spécifiques pour SQLite
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Création du moteur
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)

# Création de la session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Classe de base pour les modèles
Base = declarative_base()

def init_db():
    """
    Initialise la base de données en créant toutes les tables définies dans models.py
    """
    import models  # ⚠️ IMPORTANT : importer les modèles avant la création
    Base.metadata.create_all(bind=engine)
