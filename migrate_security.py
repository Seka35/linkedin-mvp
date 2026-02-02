import sqlite3
import os

def migrate():
    db_path = "/home/seka/Desktop/linkedin-mvp/data/prospects.db"
    print(f"🔄 Migrating database: Adding security_settings column to accounts table in {db_path}...")
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE accounts ADD COLUMN security_settings TEXT DEFAULT '{}'")
        conn.commit()
        print("✅ Migration successful!")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("⚠️ Column already exists. Skipping.")
        else:
            print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
