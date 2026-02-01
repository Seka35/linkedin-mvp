from database import SessionLocal, Action, Prospect

db = SessionLocal()

print('📊 Messages corrects:')
actions = db.query(Action).filter(Action.action_type == 'message').all()
for a in actions:
    print(f'  • {a.prospect.full_name}: "{a.message_sent}"')

print('\n📋 Statuts:')
for name in ['Typhaine', 'Liam', 'Joseph', 'J Tech']:
    p = db.query(Prospect).filter(Prospect.full_name.like(f'%{name}%')).first()
    if p:
        print(f'  • {p.full_name}: {p.status}')

db.close()
