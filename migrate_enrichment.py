"""
Migration pour Phase 6-B : Enrichissement Apify
Ajoute les champs d'enrichissement à la table prospects
"""
import sqlite3
import os

# Chemin correct vers la DB
DB_PATH = os.path.join(os.getcwd(), 'data', 'prospects.db')
print(f"🔧 Connexion à la base de données : {DB_PATH}")

if not os.path.exists(DB_PATH):
    print(f"❌ ERREUR: La base de données n'existe pas : {DB_PATH}")
    exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

new_columns = [
    ("is_enriched", "BOOLEAN DEFAULT 0"),
    ("summary", "TEXT"),
    ("email", "TEXT"),
    ("phone", "TEXT"),
    ("skills", "TEXT"),
    ("experiences", "TEXT"),
    ("education", "TEXT"),
    ("languages", "TEXT")
]

for col_name, col_type in new_columns:
    try:
        cursor.execute(f"ALTER TABLE prospects ADD COLUMN {col_name} {col_type}")
        print(f"✅ Colonne '{col_name}' ajoutée.")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print(f"ℹ️  Colonne '{col_name}' existe déjà.")
        else:
            print(f"❌ Erreur pour '{col_name}': {e}")

conn.commit()
conn.close()
print("✅ Migration terminée.")
