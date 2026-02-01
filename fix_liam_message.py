"""
Corriger le message: changer de J Tech (ID 7) vers Liam (ID 5)
"""
from database import SessionLocal, Action, Prospect

db = SessionLocal()

# Trouver le message "hello liam" qui est mal assigné
wrong_message = db.query(Action).filter(
    Action.prospect_id == 7,  # J Tech
    Action.message_sent == 'hello liam'
).first()

if wrong_message:
    print(f"Message trouvé: '{wrong_message.message_sent}' assigné à prospect ID {wrong_message.prospect_id}")
    
    # Changer vers Liam (ID 5)
    wrong_message.prospect_id = 5
    db.commit()
    
    print(f"✅ Message réassigné à Liam (ID 5)")
    
    # Mettre à jour les statuts
    liam = db.query(Prospect).filter(Prospect.id == 5).first()
    if liam:
        liam.status = 'messaged'
        print(f"✅ Liam: status → messaged")
    
    jtech = db.query(Prospect).filter(Prospect.id == 7).first()
    if jtech:
        jtech.status = 'new'
        print(f"✅ J Tech: status → new")
    
    db.commit()
    print("\n✅ Correction terminée!")
else:
    print("❌ Message non trouvé")

db.close()
