"""
Nettoyer la DB pour ne garder que les 3 premiers messages
"""
from database import SessionLocal, Action, Prospect

db = SessionLocal()

# Récupérer tous les messages
all_messages = db.query(Action).filter(
    Action.action_type == 'message'
).order_by(Action.executed_at.asc()).all()

print(f"📊 Total messages: {len(all_messages)}\n")

# Afficher tous les messages
for i, msg in enumerate(all_messages, 1):
    print(f"{i}. {msg.prospect.full_name}: '{msg.message_sent}' - {msg.executed_at}")

# Garder les 3 premiers
messages_to_keep = all_messages[:3]
messages_to_delete = all_messages[3:]

print(f"\n✅ Messages à garder: {len(messages_to_keep)}")
for msg in messages_to_keep:
    print(f"   - {msg.prospect.full_name}: '{msg.message_sent}'")

print(f"\n❌ Messages à supprimer: {len(messages_to_delete)}")
for msg in messages_to_delete:
    print(f"   - {msg.prospect.full_name}: '{msg.message_sent}'")
    db.delete(msg)

db.commit()
print("\n✅ Base de données nettoyée!")

db.close()
