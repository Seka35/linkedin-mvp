from database import SessionLocal, Prospect
import json

db = SessionLocal()
# Les 8 prospects qui posaient problème
names = ["Typhaine", "Maldonado", "Sergey", "J Tech", "Yassine", "Joseph"]

print(f"{'Nom':<30} | {'Enrichi?':<10} | {'Résumé':<10} | {'Exp scannées'}")
print("-" * 70)

for name in names:
    p = db.query(Prospect).filter(Prospect.full_name.like(f"%{name}%")).first()
    if p:
        exps = json.loads(p.experiences) if p.experiences else []
        has_summary = "OUI" if p.summary else "NON"
        print(f"{p.full_name:<30} | {str(p.is_enriched):<10} | {has_summary:<10} | {len(exps)}")
    else:
        print(f"❌ Pas trouvé: {name}")

db.close()
