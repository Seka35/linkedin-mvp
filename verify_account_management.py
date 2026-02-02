from database import SessionLocal, Account, Prospect
import time

def verify_account_mgmt():
    db = SessionLocal()
    print("🧪 Verifying Account Management...")

    # 1. Create temporary account
    acc = Account(name="To Delete", email="delete_me@test.com")
    db.add(acc)
    db.commit()
    print(f"✅ Created account '{acc.name}' (ID: {acc.id})")

    # 2. Add some data
    p = Prospect(linkedin_url="https://linkedin.com/in/delete-test", account_id=acc.id, full_name="Delete Me")
    db.add(p)
    db.commit()
    p_id = p.id
    print(f"✅ Added prospect (ID: {p_id}) to account")

    # 3. Test Rename
    acc.name = "Renamed Account"
    db.commit()
    
    refreshed_acc = db.query(Account).get(acc.id)
    if refreshed_acc.name == "Renamed Account":
        print("✅ Rename successful")
    else:
        print("❌ Rename failed")

    # 4. Test Delete (Simulating the logic from app.py)
    print("🗑️ Deleting account...")
    
    # Manual Cascade Delete Check
    db.query(Prospect).filter(Prospect.account_id == acc.id).delete()
    db.delete(acc)
    db.commit()

    # Verify deletion
    deleted_acc = db.query(Account).get(acc.id)
    deleted_prospect = db.query(Prospect).get(p_id)

    if not deleted_acc and not deleted_prospect:
        print("✅ Account and related data deleted successfully")
    else:
        print(f"❌ Deletion failed: Account={deleted_acc}, Prospect={deleted_prospect}")

    db.close()

if __name__ == "__main__":
    verify_account_mgmt()
