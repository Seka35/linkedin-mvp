import sqlite3
from datetime import datetime

DB_PATH = 'data/prospects.db'

def fix_schema():
    print(f"🔧 Starting schema fix on {DB_PATH}...")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # 1. Rename existing table
        print("📦 Renaming prospects table to prospects_old...")
        cursor.execute("ALTER TABLE prospects RENAME TO prospects_old")
        
        # 2. Create new table (WITHOUT unique constraint on linkedin_url alone)
        print("✨ Creating new prospects table...")
        # Note: We are NOT adding a composite unique constraint here for simplicity and safety, 
        # relying on application logic (scraper.py) to avoid duplicates per account.
        # But for data integrity, a UNIQUE(linkedin_url, account_id) would be better.
        # Let's stick to the model definition (no unique constraint) + app logic.
        
        cursor.execute('''
        CREATE TABLE prospects (
            id INTEGER PRIMARY KEY,
            account_id INTEGER REFERENCES accounts(id),
            linkedin_url VARCHAR NOT NULL,
            full_name VARCHAR,
            headline VARCHAR,
            company VARCHAR,
            location VARCHAR,
            profile_picture VARCHAR,
            is_enriched BOOLEAN DEFAULT 0,
            summary TEXT,
            email VARCHAR,
            phone VARCHAR,
            skills TEXT,
            experiences TEXT,
            education TEXT,
            languages TEXT,
            status VARCHAR DEFAULT 'new',
            campaign_id INTEGER REFERENCES campaigns(id),
            source VARCHAR,
            added_at DATETIME,
            last_action_at DATETIME
        )
        ''')
        
        # 3. Copy data
        print("🔄 Copying data from prospects_old...")
        # Get columns from old table to ensure we map correctly
        cursor.execute("PRAGMA table_info(prospects_old)")
        columns_info = cursor.fetchall()
        columns = [col['name'] for col in columns_info]
        
        # Build CSV string of columns
        cols_str = ", ".join(columns)
        
        # Insert data
        cursor.execute(f"INSERT INTO prospects ({cols_str}) SELECT {cols_str} FROM prospects_old")
        
        # 4. Drop old table (Optionally keep it for backup if paranoid, but let's drop to be clean)
        # print("🗑️ Dropping prospects_old...")
        # cursor.execute("DROP TABLE prospects_old") 
        # Keeping it for safety during this operation, user can delete later.
        
        conn.commit()
        print("✅ Schema fix completed successfully.")
        
    except Exception as e:
        print(f"❌ Error during schema fix: {e}")
        conn.rollback()
        # Attempt to restore if things went wrong
        try:
            cursor.execute("DROP TABLE IF EXISTS prospects")
            cursor.execute("ALTER TABLE prospects_old RENAME TO prospects")
            print("↩️ Rolled back changes.")
        except:
            pass
    finally:
        conn.close()

if __name__ == "__main__":
    fix_schema()
