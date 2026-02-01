from database.db import SessionLocal
from database.models import Prospect

db = SessionLocal()
statuses = db.query(Prospect.status).all()
db.close()

from collections import Counter
counts = Counter([s[0] for s in statuses])
print("Répartition des statuts :", counts)
print("Total :", sum(counts.values()))
