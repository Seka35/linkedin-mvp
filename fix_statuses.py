"""
Corriger les statuts des prospects
"""
from database import SessionLocal, Prospect

db = SessionLocal()

# Typhaine : connected (elle a reçu un message, donc elle était déjà connectée)
typhaine = db.query(Prospect).filter(Prospect.id == 9).first()
if typhaine:
    typhaine.status = 'connected'
    print(f"✅ Typhaine: messaged → connected")

# Joseph : followed (il a reçu un message mais c'est une connexion 2nd, pas acceptée)
joseph = db.query(Prospect).filter(Prospect.id == 2).first()
if joseph:
    joseph.status = 'followed'
    print(f"✅ Joseph: messaged → followed")

# Liam : new (il n'a PAS reçu de message, c'était J Tech qui a été confondu)
liam = db.query(Prospect).filter(Prospect.id == 7).first()
if liam:
    liam.status = 'new'
    print(f"✅ Liam: messaged → new")

db.commit()
print("\n✅ Statuts corrigés!")

db.close()
