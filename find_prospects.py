from database import SessionLocal, Prospect

db = SessionLocal()
connected_prospect = db.query(Prospect).filter(Prospect.status == 'connected').first()
if connected_prospect:
    print(f"✅ Connected Prospect Found: {connected_prospect.full_name} ({connected_prospect.linkedin_url})")
else:
    print("❌ No connected prospect found.")
    
new_prospect = db.query(Prospect).filter(Prospect.status == 'new').first()
if new_prospect:
    print(f"🆕 New Prospect Found: {new_prospect.full_name} ({new_prospect.linkedin_url})")

db.close()
