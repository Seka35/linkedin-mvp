from sqlalchemy import create_engine, text
import os
from database.models import Tag, prospect_tags, Base

# Database URL
DB_URL = "sqlite:///data/prospects.db"

def migrate():
    engine = create_engine(DB_URL)
    
    print("🔧 Migrating Tags tables...")
    try:
        # Create all tables that don't exist
        # Base.metadata.create_all(bind=engine) will create Tag and prospect_tags if they differ
        # But to be safe and explicit let's try creating them.
        Base.metadata.create_all(bind=engine)
        print("✅ Tables `tags` and `prospect_tags` created (if they didn't exist).")
        
        # Pre-populate Segments
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("🌱 Seeding default segments...")
        segments = [
            {"name": "Segment A", "color": "#28a745"}, # Green
            {"name": "Segment B", "color": "#ffc107"}, # Yellow
            {"name": "Segment C", "color": "#17a2b8"}, # Info/Blue
            {"name": "Hors Cible", "color": "#dc3545"}, # Red
        ]
        
        for seg in segments:
            exists = session.query(Tag).filter_by(name=seg['name']).first()
            if not exists:
                new_tag = Tag(name=seg['name'], color=seg['color'])
                session.add(new_tag)
                print(f"   + Created tag: {seg['name']}")
            else:
                print(f"   . Tag {seg['name']} already exists")
        
        session.commit()
        session.close()
        print("🏁 Migration & Seeding complete.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate()
