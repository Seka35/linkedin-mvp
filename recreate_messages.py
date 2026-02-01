"""
Nettoyer pour garder: Typhaine (Bonjour), Liam (hello liam), Joseph (Hello Joseph!)
"""
from database import SessionLocal, Action

db = SessionLocal()

# Supprimer TOUS les messages
all_messages = db.query(Action).filter(Action.action_type == 'message').all()
for msg in all_messages:
    db.delete(msg)
db.commit()

print("✅ Tous les messages supprimés")

# Recréer les 3 messages voulus
from datetime import datetime

# 1. Typhaine - Bonjour
typhaine_msg = Action(
    prospect_id=9,  # Typhaine
    action_type='message',
    message_sent='Bonjour',
    status='success',
    executed_at=datetime(2026, 1, 31, 7, 27, 45)
)
db.add(typhaine_msg)

# 2. Liam - hello liam
liam_msg = Action(
    prospect_id=7,  # Liam
    action_type='message',
    message_sent='hello liam',
    status='success',
    executed_at=datetime(2026, 1, 31, 7, 59, 10)
)
db.add(liam_msg)

# 3. Joseph - Hello Joseph!
joseph_msg = Action(
    prospect_id=2,  # Joseph
    action_type='message',
    message_sent='Hello Joseph!',
    status='success',
    executed_at=datetime(2026, 1, 31, 15, 54, 58)
)
db.add(joseph_msg)

db.commit()

print("✅ 3 messages recréés:")
print("   1. Typhaine: 'Bonjour'")
print("   2. Liam: 'hello liam'")
print("   3. Joseph: 'Hello Joseph!'")

db.close()
