from services.linkedin_bot import LinkedInBot
import os
from dotenv import load_dotenv

# Load env variables (cookies etc)
load_dotenv()

def deep_debug_msg():
    bot = LinkedInBot()
    try:
        bot.start()
        print("✅ Login success")
        
        target_url = "https://www.linkedin.com/in/pereiraalexandre/"
        message_to_send = "Hello from Debug Bot (Test Message Feature)"
        
        print(f"Testing send_message on {target_url}")
        
        # Test basic visit
        bot.visit_profile(target_url)
        
        # Capture HTML to analyze the "Message" button if it fails
        debug_file = "debug_profile_msg.html"
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(bot.page.content())
        print(f"HTML Dumped to {debug_file}")

        # Manually attempt to find the message button to debug selectors clearly
        # reusing logic from send_message but logging more info
        
        print("🔍 Searching for Message button interactively...")
        
        # Selectors from current code
        potential_btns = [
            bot.page.locator(".pvs-profile-actions__action .artdeco-button--primary[aria-label*='Message']"),
            bot.page.locator("a[href*='/messaging/compose']"),
            bot.page.get_by_text("Message", exact=True),
            bot.page.get_by_text("Envoyer un message", exact=True)
        ]
        
        found_btn = None
        for i, btn in enumerate(potential_btns):
            print(f"Checking selector {i}...")
            if btn.first.is_visible():
                print(f"✅ Found via selector {i}")
                found_btn = btn.first
                break
        
        if found_btn:
            print("Clicking Message button...")
            
            # Just click and wait for effect (overlay or navigation)
            try:
                found_btn.click()
            except Exception as e:
                print(f"Click warning: {e}")
                # Fallback JS click
                bot.page.evaluate("(el) => el.click()", found_btn.element_handle())

            bot._random_delay(2, 4)
            print(f"Current URL after click: {bot.page.url}")
            
            print("Checking for editor...")
            # Wait for editor to appear
            try:
                # Increased timeout
                bot.page.wait_for_selector("div.msg-form__contenteditable, div[role='textbox']", timeout=15000)
            except:
                print("Wait for editor timeout.")

            editor = bot.page.locator("div.msg-form__contenteditable").first
            if not editor.is_visible():
                print("Editor not visible with .msg-form__contenteditable")
                editor = bot.page.locator("div[role='textbox'][aria-label*='Write a message']").first
            
            if editor.is_visible():
                print("✅ Editor found!") 
                editor.click()
                editor.fill(message_to_send)
                print("Text filled.")
                
                # Check Send button
                send_btn = bot.page.locator("button.msg-form__send-button").first
                if not send_btn.is_visible():
                     send_btn = bot.page.locator("button[type='submit']").first
                
                if send_btn.is_visible():
                    print("✅ Send button found!")
                    # Uncomment next line to actually send
                    # send_btn.click()
                else:
                    print("❌ Send button NOT found.")
            else:
                print("❌ Editor NOT found.")
                # Dump HTML again if editor fails
                with open("debug_msg_editor.html", "w", encoding="utf-8") as f:
                    f.write(bot.page.content())

        else:
            print("❌ Message button NOT found.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # bot.close() method doesn't exist, assume we just stop the playwright instance if possible or do nothing
        if hasattr(bot, 'browser') and bot.browser:
             bot.browser.close()
        if hasattr(bot, 'playwright') and bot.playwright:
             bot.playwright.stop()

if __name__ == "__main__":
    deep_debug_msg()
