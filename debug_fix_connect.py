from services.linkedin_bot import LinkedInBot
import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()

# Script manuel pour tester le fix "Connection Button"
# Usage: python debug_fix_connect.py [URL_PROFIL]

def test_connection_fix(profile_url=None):
    if not profile_url:
        print("❌ Spécifiez une URL de profil à tester.")
        print("Usage: python debug_fix_connect.py <linkedin_url>")
        return

    print("🚀 Démarrage du test de connexion (mode FIX)...")
    print(f"Cible: {profile_url}")
    
    bot = LinkedInBot(headless=False)
    
    try:
        started = bot.start()
        if not started:
            print("❌ Impossible de démarrer le bot (Cookie HS ?)")
            return

        print("\n--- 1. Test de visite et extraction ID ---")
        success = bot.visit_profile(profile_url)
        if not success:
            print("❌ Visite échouée")
            return
            
        # Sauvegarder le HTML immédiatement après la visite pour debug des sélecteurs
        # debug_file = "debug_profile_valid.html"
        # with open(debug_file, "w", encoding="utf-8") as f:
        #     f.write(bot.page.content())
        # print(f"📄 HTML du PROFIL sauvegardé dans {debug_file} (avant tentative connexion).")
            
        # Test explicite de l'extraction ID pour debug
        profile_id = bot._extract_profile_id()
        if profile_id:
            print(f"✅ SUCCÈS: ID extrait = {profile_id}")
        else:
            print("⚠️ AVERTISSEMENT: ID non trouvé par la nouvelle méthode.")

        print("\n--- 2. Test send_connection_request (Méthode Directe) ---")
        # On relance la méthode complète pour voir si elle enchaîne bien
        result = bot.send_connection_request(profile_url)
        
        if result:
            print("\n🎉 SUCCÈS TOTAL: La demande a été envoyée (ou modale ouverte).")
        else:
            print("\n❌ ÉCHEC: La connexion n'a pas pu être faite.")
            # Sauvegarder le HTML pour debug
            debug_file = "debug_profile_dump.html"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(bot.page.content())
            print(f"📄 HTML de la page sauvegardé dans {debug_file} pour analyse.")
            
    except Exception as e:
        print(f"❌ Exception durant le test: {e}")
    finally:
        print("\n⏳ Fin du test dans 10 secondes...")
        time.sleep(10)
        bot.stop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # URL de test par défaut (ex: un profil open networker ou autre)
        # Mais mieux vaut laisser l'utilisateur choisir
        url = input("Entrez l'URL LinkedIn du profil à tester: ")
    
    test_connection_fix(url)
