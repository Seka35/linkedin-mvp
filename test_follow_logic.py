from services.linkedin_bot import LinkedInBot
import os
from dotenv import load_dotenv
import time

load_dotenv()

def test_follow():
    print("🚀 Initializing Bot for FOLLOW check (Headless=False)...")
    bot = LinkedInBot(headless=False)
    
    try:
        bot.start()
        print("✅ Bot started")
        
        # Typhaine's URL (known to have Follow primary)
        target = "https://www.linkedin.com/in/typhaine-morvan/?locale=en"
        
        print(f"Testing send_connection_request on {target}")
        print("Expecting: 'Connect' NOT found (or in menu), fallback to 'Follow' if necessary.")
        
        # We pass a dummy message, but it should be ignored as we removed note support
        # logic returns (bool, status_string)
        success, status = bot.send_connection_request(target, "Hello")
        
        print(f"🏁 Result: Success={success}, Status={status}")
        
        if status == 'followed':
            print("🎉 SUCCESS: Bot correctly identified and clicked 'Follow'.")
        elif status == 'connected':
             print("ℹ️ RESULT: Bot managed to 'Connect' (maybe via More menu?).")
        else:
            print("❌ FAILED to Connect or Follow.")

        print("⏳ Waiting 10s for visual verification...")
        time.sleep(10)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if hasattr(bot, 'browser') and bot.browser:
             bot.browser.close()
        if hasattr(bot, 'playwright') and bot.playwright:
             bot.playwright.stop()

if __name__ == "__main__":
    test_follow()
