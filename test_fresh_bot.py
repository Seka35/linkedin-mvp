"""
Test SIMPLE et PROPRE: Message à Typhaine
Avec un bot complètement frais
"""
from dotenv import load_dotenv
load_dotenv()  # IMPORTANT: Charger les variables d'environnement

from services.linkedin_bot import LinkedInBot
from database import SessionLocal, Prospect, Action
from datetime import datetime
import time

print("=" * 70)
print("TEST FINAL: Message à Typhaine (session fraîche)")
print("=" * 70)

# Initialiser un bot FRAIS
print("\n🚀 Démarrage d'un bot complètement neuf...")
bot = LinkedInBot(headless=False)

try:
    bot.start()
    print("✅ Bot démarré avec succès\n")
    
    # URL de Typhaine
    typhaine_url = "https://www.linkedin.com/in/typhaine-morvan/?locale=en"
    message = "Hello again!"
    
    print(f"📤 Envoi du message à Typhaine...")
    print(f"   URL: {typhaine_url}")
    print(f"   Message: '{message}'\n")
    
    # Envoyer le message
    success = bot.send_message(typhaine_url, message)
    
    if success:
        print("\n✅ SUCCESS! Le bot a envoyé le message.")
        
        # Enregistrer dans la DB
        db = SessionLocal()
        typhaine = db.query(Prospect).filter(
            Prospect.linkedin_url.like('%typhaine%')
        ).first()
        
        if typhaine:
            action = Action(
                prospect_id=typhaine.id,
                action_type='message',
                message_sent=message,
                status='success',
                executed_at=datetime.utcnow()
            )
            db.add(action)
            typhaine.status = 'messaged'
            db.commit()
            print("✅ Message enregistré dans la DB")
        
        db.close()
        
        print("\n" + "=" * 70)
        print("🎉 TEST RÉUSSI!")
        print("=" * 70)
        print("\n👉 Vérifie http://127.0.0.1:5000/messages")
        
    else:
        print("\n❌ FAILED: Le bot n'a pas réussi à envoyer le message")
    
    print("\n⏳ Attente de 10s pour vérification visuelle...")
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
