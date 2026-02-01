"""
Script de réparation de la DB - Phase 5
Ajoute les colonnes manquantes si nécessaire.
"""
import sqlite3
import os

# Chemin absolu vers la DB pour éviter les erreurs de chemin
DB_PATH = os.path.join(os.getcwd(), 'linkedin_bot.db')

print(f"🔧 Connexion à la base de données : {DB_PATH}")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 1. Vérifier et ajouter campaign_id à prospects
try:
    cursor.execute("ALTER TABLE prospects ADD COLUMN campaign_id INTEGER")
    print("✅ Colonne 'campaign_id' ajoutée à la table 'prospects'")
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e).lower():
        print("ℹ️  Colonne 'campaign_id' existe déjà dans 'prospects'")
    else:
        print(f"❌ Erreur sur prospects: {e}")

# 2. Vérifier et ajouter message_delay_days à campaigns
try:
    cursor.execute("ALTER TABLE campaigns ADD COLUMN message_delay_days INTEGER DEFAULT 3")
    print("✅ Colonne 'message_delay_days' ajoutée à la table 'campaigns'")
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e).lower():
        print("ℹ️  Colonne 'message_delay_days' existe déjà dans 'campaigns'")
    else:
        print(f"❌ Erreur sur campaigns: {e}")

conn.commit()
conn.close()
print("✅ Migration terminée.")
