from database import SessionLocal, Action

db = SessionLocal()
msgs = db.query(Action).filter(
    Action.action_type == 'message'
).order_by(Action.executed_at.desc()).all()

print(f'📊 Messages dans la base de données: {len(msgs)}\n')

for i, m in enumerate(msgs, 1):
    print(f'{i}. {m.prospect.full_name}')
    print(f'   Message: "{m.message_sent}"')
    print(f'   Date: {m.executed_at.strftime("%d/%m/%Y %H:%M")}')
    print(f'   Statut: {m.status}')
    print()

db.close()
