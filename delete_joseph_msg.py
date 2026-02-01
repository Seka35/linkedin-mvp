from database import SessionLocal, Action

db = SessionLocal()
joseph_msg = db.query(Action).filter(
    Action.prospect_id == 2, 
    Action.action_type == 'message'
).first()

if joseph_msg:
    db.delete(joseph_msg)
    db.commit()
    print('✅ Message de Joseph supprimé')
else:
    print('Aucun message trouvé')
    
db.close()
