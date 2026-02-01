"""
Migration de la base de données pour Phase 5
Ajoute les nouveaux champs: campaign_id, message_delay_days
"""
import sqlite3

# Connexion à la DB
conn = sqlite3.connect('linkedin_bot.db')
cursor = conn.cursor()

print("🔧 Migration de la base de données...")

# 1. Ajouter campaign_id à prospects
try:
    cursor.execute("ALTER TABLE prospects ADD COLUMN campaign_id INTEGER")
    print("✅ Ajout de 'campaign_id' à prospects")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("ℹ️  'campaign_id' existe déjà dans prospects")
    else:
        print(f"❌ Erreur: {e}")

# 2. Ajouter message_delay_days à campaigns
try:
    cursor.execute("ALTER TABLE campaigns ADD COLUMN message_delay_days INTEGER DEFAULT 3")
    print("✅ Ajout de 'message_delay_days' à campaigns")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("ℹ️  'message_delay_days' existe déjà dans campaigns")
    else:
        print(f"❌ Erreur: {e}")

# 3. Mettre à jour les campagnes existantes
cursor.execute("UPDATE campaigns SET message_delay_days = 3 WHERE message_delay_days IS NULL")
print(f"✅ {cursor.rowcount} campagne(s) mise(s) à jour avec délai par défaut (3 jours)")

conn.commit()
conn.close()

print("\n✅ Migration terminée !")
