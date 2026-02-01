from services.linkedin_bot import LinkedInBot
import os
from dotenv import load_dotenv

load_dotenv()

def test_msg():
    bot = LinkedInBot()
    try:
        bot.start()
        print("✅ Bot started")
        
        target = "https://id.linkedin.com/in/florian-ogier-409bb920"
        msg = "Hello Florian, ceci est un test automatique du bot. Bonne journée !"
        
        print(f"Testing send_message on {target}")
        result = bot.send_message(target, msg)
        
        if result:
            print("🎉 Success: Message UI handled correctly.")
        else:
            print("❌ Failed.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if hasattr(bot, 'browser') and bot.browser:
             bot.browser.close()
        if hasattr(bot, 'playwright') and bot.playwright:
             bot.playwright.stop()

if __name__ == "__main__":
    test_msg()
