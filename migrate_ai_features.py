from database.db import SessionLocal, engine, Base
from database.models import Settings, Campaign
from sqlalchemy import text
import sqlalchemy

def migrate():
    print("Starting migration for AI features...")
    
    # 1. Create tables that don't exist (Settings)
    Base.metadata.create_all(bind=engine)
    print("Checked/Created tables.")

    # 2. Add column use_ai_customization to campaigns if not exists
    session = SessionLocal()
    try:
        # Check if column exists
        result = session.execute(text("PRAGMA table_info(campaigns)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'use_ai_customization' not in columns:
            print("Adding column 'use_ai_customization' to 'campaigns' table...")
            session.execute(text("ALTER TABLE campaigns ADD COLUMN use_ai_customization BOOLEAN DEFAULT 0"))
            session.commit()
            print("Column added.")
        else:
            print("Column 'use_ai_customization' already exists.")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    migrate()
