from database.db import SessionLocal
from database.models import Settings
from services.ai_service import DEFAULT_PROMPT

def update_prompt():
    db = SessionLocal()
    setting = db.query(Settings).filter(Settings.key == 'system_prompt').first()
    
    if setting:
        print("Updating existing system prompt in DB...")
        setting.value = DEFAULT_PROMPT
    else:
        print("Creating new system prompt in DB...")
        setting = Settings(key='system_prompt', value=DEFAULT_PROMPT)
        db.add(setting)
    
    db.commit()
    db.close()
    print("✅ System prompt updated successfully.")

if __name__ == "__main__":
    update_prompt()
