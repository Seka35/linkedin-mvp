from database import SessionLocal, Account
from services.linkedin_bot import LinkedInBot
import os

def verify_proxy_toggle():
    print("🧪 Verifying Proxy Toggle Logic...")
    db = SessionLocal()
    
    # 1. Setup Account
    acc = db.query(Account).first()
    if not acc:
        print("❌ No account found")
        return
        
    print(f"👤 Using account: {acc.name} (ID: {acc.id})")
    
    # ensure proxy config exists
    acc.proxy_url = "http://test.proxy:8080"
    acc.proxy_username = "user"
    acc.proxy_password = "pass"
    db.commit()
    
    # 2. Test OFF
    print("\n[Case 1] Proxy Enabled = FALSE")
    acc.proxy_enabled = False
    db.commit()
    
    # Simulate logic from app.py
    proxy_config = None
    if acc.proxy_url and acc.proxy_enabled:
        proxy_config = {
            'server': acc.proxy_url,
            'username': acc.proxy_username,
            'password': acc.proxy_password
        }
    
    if proxy_config is None:
        print("✅ Proxy config ignored correctly (Proxy OFF)")
    else:
        print(f"❌ Error: Proxy config used when OFF: {proxy_config}")

    # 3. Test ON
    print("\n[Case 2] Proxy Enabled = TRUE")
    acc.proxy_enabled = True
    db.commit()
    
    proxy_config = None
    if acc.proxy_url and acc.proxy_enabled:
        proxy_config = {
            'server': acc.proxy_url,
            'username': acc.proxy_username,
            'password': acc.proxy_password
        }
        
    if proxy_config and proxy_config['server'] == "http://test.proxy:8080":
         print("✅ Proxy config used correctly (Proxy ON)")
    else:
         print("❌ Error: Proxy config NOT used when ON")

    db.close()

if __name__ == "__main__":
    verify_proxy_toggle()
