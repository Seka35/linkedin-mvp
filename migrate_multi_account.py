import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

DB_PATH = 'data/prospects.db'

def run_migration():
    print(f"🚀 Démarrage de la migration multi-comptes sur {DB_PATH}...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Créer la table accounts
    print("Creating 'accounts' table...")
    try:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY,
            name VARCHAR,
            email VARCHAR UNIQUE NOT NULL,
            li_at_cookie TEXT,
            proxy_url VARCHAR,
            proxy_username VARCHAR,
            proxy_password VARCHAR,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME
        )
        ''')
    except Exception as e:
        print(f"Error creating accounts table: {e}")

    # 2. Vérifier si un compte par défaut existe, sinon le créer depuis .env
    print("Checking for default account...")
    default_email = os.getenv('LINKEDIN_EMAIL', 'default@example.com')
    default_cookie = os.getenv('LINKEDIN_LI_AT_COOKIE', '')
    proxy_url = os.getenv('PROXY_URL', '')
    proxy_user = os.getenv('PROXY_USERNAME', '')
    proxy_pass = os.getenv('PROXY_PASSWORD', '')
    
    cursor.execute("SELECT id FROM accounts WHERE email = ?", (default_email,))
    account = cursor.fetchone()
    
    if not account:
        print(f"Creating default account for {default_email}...")
        cursor.execute('''
        INSERT INTO accounts (name, email, li_at_cookie, proxy_url, proxy_username, proxy_password, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('Default Account', default_email, default_cookie, proxy_url, proxy_user, proxy_pass, datetime.utcnow()))
        account_id = cursor.lastrowid
    else:
        print(f"Default account found (ID: {account[0]}).")
        account_id = account[0]

    # 3. Ajouter la colonne account_id aux tables prospects et campaigns
    # SQLite ne supporte pas ADD COLUMN avec IF NOT EXISTS de manière simple pour les FK, 
    # mais on peut tenter l'ajout et ignorer l'erreur si la colonne existe.
    
    tables_to_migrate = ['prospects', 'campaigns']
    
    for table in tables_to_migrate:
        print(f"Migrating table {table}...")
        try:
            # Vérifier si la colonne existe déjà
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [info[1] for info in cursor.fetchall()]
            
            if 'account_id' not in columns:
                print(f"Adding account_id column to {table}...")
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN account_id INTEGER REFERENCES accounts(id)")
                
                # Assigner le compte par défaut à tous les enregistrements existants
                print(f"Updating existing records in {table} to account_id={account_id}...")
                cursor.execute(f"UPDATE {table} SET account_id = ?", (account_id,))
            else:
                print(f"Column account_id already exists in {table}.")
                
        except Exception as e:
            print(f"Error migrating {table}: {e}")

    # 4. Enlever la contrainte UNIQUE sur linkedin_url dans prospects si elle existe (c'est compliqué en SQLite)
    # En SQLite, pour modifier une contrainte, il faut souvent recréer la table.
    # Pour l'instant, on va laisser la contrainte UNIQUE telle quelle car elle est probablement sur l'index.
    # Si on a besoin de doublons (même prospect sur plusieurs comptes), il faudra recréer la table.
    # Pour ce MVP, on assume que la contrainte UNIQUE est globale. 
    # TODO: Pour une vraie séparation, il faudrait recréer la table prospects avec une contrainte UNIQUE(linkedin_url, account_id).
    
    conn.commit()
    conn.close()
    print("✅ Migration terminée avec succès.")

if __name__ == "__main__":
    run_migration()
