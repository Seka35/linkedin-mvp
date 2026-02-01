from services.linkedin_bot import LinkedInBot
import time
import sys

# Script de debug manuel demandé par l'utilisateur
# Lance le bot, va sur le profil, et attend indéfiniment pour laisser l'humain cliquer.

def start_debug():
    print("🚀 Démarrage du mode DEBUG MANUEL...")
    bot = LinkedInBot(headless=False) # Force visible
    
    if bot.start():
        print("✅ Bot connecté.")
        target_url = "https://www.linkedin.com/in/pereiraalexandre/?locale=en"
        print(f"👁️ Visite du profil : {target_url}")
        bot.visit_profile(target_url)
        
        print("\n" + "="*50)
        print("🛑 NAVIGATEUR EN PAUSE - À VOUS DE JOUER !")
        print("1. Vous pouvez cliquer manuellement sur 'Connect' dans la fenêtre ouverte.")
        print("2. Observez la console du navigateur (F12) pour voir les erreurs éventuelles.")
        print("3. Pour quitter, appuyez sur CTRL+C ici.")
        print("="*50 + "\n")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Arrêt du debug.")
            bot.stop()
    else:
        print("❌ Échec de connexion du bot.")

if __name__ == "__main__":
    start_debug()
