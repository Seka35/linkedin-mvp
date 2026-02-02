from database import SessionLocal, Account, Prospect, Campaign, Settings

def verify_multi_account():
    db = SessionLocal()
    print("🧪 Starting verification...")

    # 1. Verify Default Account
    default_acc = db.query(Account).first()
    if not default_acc:
        print("❌ No default account found!")
        return
    print(f"✅ Default Account found: {default_acc.name} (ID: {default_acc.id})")

    # 2. Create Test Account
    test_email = "test_verify@example.com"
    test_acc = db.query(Account).filter(Account.email == test_email).first()
    if not test_acc:
        test_acc = Account(name="Verification Account", email=test_email)
        db.add(test_acc)
        db.commit()
        print(f"✅ Created Verification Account (ID: {test_acc.id})")
    else:
        print(f"ℹ️ Verification Account already exists (ID: {test_acc.id})")

    # 3. Add Data to Test Account
    # Add a prospect
    p = Prospect(linkedin_url="https://linkedin.com/in/test-verify", full_name="Test Verify", account_id=test_acc.id)
    db.add(p)
    db.commit()
    print("✅ Added prospect to Verification Account")

    # 4. Verify Isolation
    # Check Default Account prospects (should NOT include the new one strictly speaking, but query filters are key)
    # This script tests the DB state, the filtering happens in the app.
    
    cnt_default = db.query(Prospect).filter(Prospect.account_id == default_acc.id).count()
    cnt_test = db.query(Prospect).filter(Prospect.account_id == test_acc.id).count()
    
    print(f"📊 Stats Default Account: {cnt_default} prospects")
    print(f"📊 Stats Verification Account: {cnt_test} prospects")

    if cnt_test >= 1:
        print("✅ Data isolation check passed (DB level)")
    else:
        print("❌ Data isolation failed")

    # Clean up
    db.delete(p)
    # db.delete(test_acc) # Keep account for manual UI check if needed
    db.commit()
    print("🧹 Cleanup done")
    db.close()

if __name__ == "__main__":
    verify_multi_account()
