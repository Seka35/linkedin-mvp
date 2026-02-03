from database.db import engine, Base
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("PRAGMA table_info(actions)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'source' not in columns:
                print("Migrating: Adding 'source' column to 'actions' table...")
                conn.execute(text("ALTER TABLE actions ADD COLUMN source VARCHAR"))
                print("Migration successful: 'source' column added.")
            else:
                print("Migration skipped: 'source' column already exists.")
                
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
