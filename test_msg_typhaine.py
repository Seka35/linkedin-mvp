from services.linkedin_bot import LinkedInBot
import os
from dotenv import load_dotenv
import time

load_dotenv()

def test_msg():
    print("🚀 Initializing Bot in VISUAL mode (Headless=False)...")
    bot = LinkedInBot(headless=False)
    try:
        bot.start()
        print("✅ Bot started")
        
        target = "https://www.linkedin.com/in/typhaine-morvan/?locale=en"
        msg = "Bonjour"
        
        print(f"Testing send_message on {target}")
        result = bot.send_message(target, msg)
        
        if result:
            print("🎉 Success: Message UI handled correctly.")
            
            # Update DB to reflect success in Dashboard
            from database import SessionLocal, Prospect, Action
            from datetime import datetime
            
            db = SessionLocal()
            prospect = db.query(Prospect).filter(Prospect.linkedin_url.like("%typhaine-morvan%")).first()
            if prospect:
                print(f"📝 Logging action for {prospect.full_name}...")
                action = Action(
                    prospect_id=prospect.id,
                    action_type='message',
                    message_sent=msg,
                    status='success',
                    executed_at=datetime.utcnow()
                )
                db.add(action)
                prospect.status = 'messaged'
                prospect.last_action_at = datetime.utcnow()
                db.commit()
                print("✅ Database updated! Check dashboard.")
            else:
                print("⚠️ Prospect not found in DB, skipping log.")
            db.close()

        else:
            print("❌ Failed.")
            
        print("⏳ Waiting 10s before closing for visual check...")
        time.sleep(10)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if hasattr(bot, 'browser') and bot.browser:
             bot.browser.close()
        if hasattr(bot, 'playwright') and bot.playwright:
             bot.playwright.stop()

if __name__ == "__main__":
    test_msg()
