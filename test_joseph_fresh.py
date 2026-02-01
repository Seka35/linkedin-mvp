"""
Test: Message à Joseph avec session fraîche
"""
from dotenv import load_dotenv
load_dotenv()

from services.linkedin_bot import LinkedInBot
from database import SessionLocal, Prospect, Action
from datetime import datetime
import time

print("=" * 70)
print("TEST: Message à Joseph Choueifaty (session fraîche)")
print("=" * 70)

# Démarrer bot frais
print("\n🚀 Démarrage d'un bot frais...")
bot = LinkedInBot(headless=False)

try:
    bot.start()
    print("✅ Bot démarré\n")
    
    # URL de Joseph
    joseph_url = "https://www.linkedin.com/in/josephchoueifaty/?locale=en"
    message = "Hello Joseph!"
    
    print(f"📤 Envoi du message...")
    print(f"   Prospect: Joseph Choueifaty")
    print(f"   Message: '{message}'\n")
    
    # Envoyer le message
    success = bot.send_message(joseph_url, message)
    
    if success:
        print("\n✅ SUCCESS! Message envoyé.")
        
        # Enregistrer dans la DB
        db = SessionLocal()
        joseph = db.query(Prospect).filter(Prospect.id == 2).first()
        
        if joseph:
            action = Action(
                prospect_id=joseph.id,
                action_type='message',
                message_sent=message,
                status='success',
                executed_at=datetime.now()
            )
            db.add(action)
            joseph.status = 'messaged'
            db.commit()
            print("✅ Message enregistré dans la DB")
        
        db.close()
        
        print("\n" + "=" * 70)
        print("🎉 TEST RÉUSSI!")
        print("=" * 70)
        print("\n👉 Vérifie http://127.0.0.1:5000/messages")
        
    else:
        print("\n❌ FAILED: Le bot n'a pas réussi")
        print("   Raisons possibles:")
        print("   - Joseph est 3rd (popup Premium)")
        print("   - Bouton Message non cliquable")
    
    print("\n⏳ Attente de 10s pour vérification...")
    time.sleep(10)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    print("\n🔒 Fermeture du bot...")
    if hasattr(bot, 'browser') and bot.browser:
        bot.browser.close()
    if hasattr(bot, 'playwright') and bot.playwright:
        bot.playwright.stop()
    print("✅ Bot fermé")
