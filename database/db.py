"""
Gestion de la connexion à la base de données SQLite.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
import os

# Declare Base here so it can be imported by models.py
Base = declarative_base()

# Chemin vers la DB
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'prospects.db')

# Créer le dossier data si inexistant
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Créer engine SQLite
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)

# Session factory
SessionLocal = scoped_session(sessionmaker(bind=engine))

def init_db(app=None):
    """Initialiser la base de données (créer tables)"""
    # Import des modèles pour qu'ils soient enregistrés dans Base.metadata
    from . import models  # noqa
    Base.metadata.create_all(bind=engine)
    print("✅ Base de données initialisée")

def get_db():
    """Obtenir une session de base de données"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
