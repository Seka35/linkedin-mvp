from database import SessionLocal, Account, Prospect

def test_duplicate_url():
    db = SessionLocal()
    print("🧪 Testing duplicate URL across accounts...")
    
    url = "https://www.linkedin.com/in/test-unique-constraint"
    
    # Get Account 1 and 2
    acc1 = db.query(Account).get(1)
    acc2 = db.query(Account).get(2)
    
    if not acc1 or not acc2:
        print("❌ Need at least 2 accounts for this test.")
        return

    # Clean up previous test
    db.query(Prospect).filter(Prospect.linkedin_url == url).delete()
    db.commit()

    try:
        # Add to Account 1
        p1 = Prospect(linkedin_url=url, full_name="Test User", account_id=acc1.id)
        db.add(p1)
        db.commit()
        print(f"✅ Added to Account {acc1.id}")
        
        # Add to Account 2
        p2 = Prospect(linkedin_url=url, full_name="Test User", account_id=acc2.id)
        db.add(p2)
        db.commit()
        print(f"✅ Added to Account {acc2.id}")
        
        print("🎉 SUCCESS: Same URL added to multiple accounts.")
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        db.rollback()
    finally:
        # Cleanup
        db.query(Prospect).filter(Prospect.linkedin_url == url).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    test_duplicate_url()
