from sqlalchemy import create_engine, text
import os

# Database URL
DB_URL = "sqlite:///data/prospects.db"

def migrate():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        print("🔧 Checking database schema...")
        
        # Helper to check if column exists
        def column_exists(table, column):
            result = conn.execute(text(f"PRAGMA table_info({table})"))
            for row in result:
                if row[1] == column:
                    return True
            return False

        # Columns to add
        new_columns = [
            ("connections_count", "INTEGER"),
            ("followers_count", "INTEGER"),
            ("is_premium", "BOOLEAN"),
            ("is_creator", "BOOLEAN"), 
            ("is_verified", "BOOLEAN"),
            ("company_size", "VARCHAR"),
            ("industry", "VARCHAR"),
            ("years_of_experience", "FLOAT"),
            ("raw_data", "TEXT")
        ]

        for col_name, col_type in new_columns:
            if not column_exists("prospects", col_name):
                print(f"➕ Adding column: {col_name} ({col_type})")
                try:
                    conn.execute(text(f"ALTER TABLE prospects ADD COLUMN {col_name} {col_type}"))
                    print(f"✅ Added {col_name}")
                except Exception as e:
                    print(f"❌ Error adding {col_name}: {e}")
            else:
                print(f"Example: {col_name} already exists.")
        
        conn.commit()
        print("🏁 Migration complete.")

if __name__ == "__main__":
    migrate()
