# backend_produits/main.py

from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import uuid
import shutil
from pathlib import Path

# Imports pour votre projet
import crud as crud
import models as models
import schemas as schemas
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Application de gestion des produits")

# Créer le dossier uploads s'il n'existe pas
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Servir les fichiers statiques (images)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Configuration CORS améliorée
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://frontend-produit.vercel.app",
        "*"  # Pour le développement - retirez en production
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Route de santé pour réveiller le serveur (important pour Render)
@app.get("/health")
def health_check():
    return {"status": "OK", "message": "Server is running"}

@app.get("/")
def read_root():
    return {"message": "Bienvenue dans l'application de gestion des produits!"}

# Dépendance pour la base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Fonction pour sauvegarder l'image
async def save_upload_file(upload_file: UploadFile) -> str:
    """Sauvegarde le fichier uploadé et retourne l'URL"""
    if upload_file.filename:
        # Générer un nom unique pour éviter les conflits
        file_extension = os.path.splitext(upload_file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Sauvegarder le fichier
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        
        # Retourner l'URL relative
        return f"/uploads/{unique_filename}"
    return None

# Créer un produit avec upload d'image
@app.post("/products/", response_model=schemas.Product)
async def create_product(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Créer un nouveau produit avec image optionnelle"""
    try:
        # Validation de l'image si fournie
        image_url = None
        if image and image.filename:
            # Vérifier le type de fichier
            if not image.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="Le fichier doit être une image")
            
            # Vérifier la taille (max 5MB)
            if image.size and image.size > 5 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="L'image ne doit pas dépasser 5MB")
            
            # Sauvegarder l'image
            image_url = await save_upload_file(image)
        
        # Créer l'objet produit
        product_data = schemas.ProductCreate(
            name=name,
            description=description or "",
            price=price,
            image=image_url
        )
        
        # Créer le produit en base
        created_product = crud.create_product(db=db, product=product_data)
        return created_product
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création: {str(e)}")

# Lire tous les produits
@app.get("/products/", response_model=List[schemas.Product])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        products = crud.get_products(db, skip=skip, limit=limit)
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")

# Lire un produit par ID
@app.get("/products/{product_id}", response_model=schemas.Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    try:
        db_product = crud.get_product(db, product_id=product_id)
        if db_product is None:
            raise HTTPException(status_code=404, detail="Produit non trouvé")
        return db_product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")

# Modifier un produit avec image
@app.put("/products/{product_id}", response_model=schemas.Product)
async def update_product(
    product_id: int,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Modifier un produit existant avec image optionnelle"""
    try:
        # Vérifier que le produit existe
        existing_product = crud.get_product(db, product_id=product_id)
        if existing_product is None:
            raise HTTPException(status_code=404, detail="Produit non trouvé")
        
        # Traitement de l'image si fournie
        image_url = existing_product.image  # Garder l'ancienne image par défaut
        if image and image.filename:
            # Vérifier le type de fichier
            if not image.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="Le fichier doit être une image")
            
            # Vérifier la taille
            if image.size and image.size > 5 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="L'image ne doit pas dépasser 5MB")
            
            # Supprimer l'ancienne image si elle existe
            if existing_product.image:
                old_image_path = existing_product.image.replace("/uploads/", "")
                old_file_path = os.path.join(UPLOAD_DIR, old_image_path)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            
            # Sauvegarder la nouvelle image
            image_url = await save_upload_file(image)
        
        # Créer l'objet de mise à jour
        product_data = schemas.ProductCreate(
            name=name,
            description=description or "",
            price=price,
            image=image_url
        )
        
        # Mettre à jour le produit
        updated_product = crud.update_product(db, product_id=product_id, product=product_data)
        if updated_product is None:
            raise HTTPException(status_code=404, detail="Échec de la mise à jour")
        
        return updated_product
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour: {str(e)}")

# Supprimer un produit
@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    try:
        # Récupérer le produit pour supprimer son image
        existing_product = crud.get_product(db, product_id=product_id)
        if existing_product and existing_product.image:
            image_path = existing_product.image.replace("/uploads/", "")
            file_path = os.path.join(UPLOAD_DIR, image_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Supprimer le produit de la base
        success = crud.delete_product(db, product_id=product_id)
        if not success:
            raise HTTPException(status_code=404, detail="Produit non trouvé")
        
        return JSONResponse(content={"message": "Produit supprimé avec succès"})
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")

# Route pour tester l'upload
@app.post("/test-upload/")
async def test_upload(file: UploadFile = File(...)):
    """Route de test pour l'upload de fichiers"""
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": file.size if hasattr(file, 'size') else "Unknown"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)