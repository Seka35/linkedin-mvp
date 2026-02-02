import sqlite3
import os

DB_PATH = 'data/prospects.db'

def run_migration():
    print(f"🚀 Adding 'user_agent' column to accounts table in {DB_PATH}...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(accounts)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'user_agent' not in columns:
            print("Adding user_agent column...")
            cursor.execute("ALTER TABLE accounts ADD COLUMN user_agent TEXT")
            print("✅ Column added.")
        else:
            print("ℹ️ Column user_agent already exists.")
            
        conn.commit()
    except Exception as e:
        print(f"❌ Error migrating accounts table: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
