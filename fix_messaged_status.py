from database.db import SessionLocal
from database.models import Prospect

db = SessionLocal()
# Trouver les prospects 'messaged' qui traînent
to_fix = db.query(Prospect).filter(Prospect.status == 'messaged').all()

for p in to_fix:
    print(f"Correction statut: {p.full_name} ({p.status} -> new)")
    p.status = 'new'

db.commit()
db.close()
