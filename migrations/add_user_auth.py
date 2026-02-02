"""
Migration script: Add User table and initialize default user
Username: Seka
Password: 1103 Rcxx (hashed with bcrypt)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db import engine, SessionLocal, Base
from database.models import User
import bcrypt

def migrate():
    print("🔧 Creating User table...")
    Base.metadata.create_all(engine, tables=[User.__table__])
    
    db = SessionLocal()
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == 'Seka').first()
    
    if existing_user:
        print("✅ User 'Seka' already exists. Skipping initialization.")
    else:
        # Hash the password
        password = "1103 Rcxx"
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create default user
        default_user = User(
            username='Seka',
            password_hash=password_hash
        )
        
        db.add(default_user)
        db.commit()
        print("✅ Default user 'Seka' created successfully!")
    
    db.close()
    print("✅ Migration complete!")

if __name__ == '__main__':
    migrate()
