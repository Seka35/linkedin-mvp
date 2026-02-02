#!/usr/bin/env python3
"""
Script de test pour vérifier que le proxy fonctionne correctement
"""
import os
from dotenv import load_dotenv
from services.proxy_manager import ProxyManager
from playwright.sync_api import sync_playwright
import sys

# Charger les variables d'environnement
load_dotenv()

def test_proxy_config():
    """Tester la configuration du proxy"""
    print("=" * 60)
    print("🔍 TEST DE CONFIGURATION PROXY")
    print("=" * 60)
    
    proxy_manager = ProxyManager()
    
    print(f"\n📋 Configuration détectée:")
    print(f"   Host: {proxy_manager.host}")
    print(f"   Username: {proxy_manager.username}")
    print(f"   Password: {'*' * len(proxy_manager.password) if proxy_manager.password else 'Non défini'}")
    print(f"   Port: {proxy_manager.port}")
    
    proxy_config = proxy_manager.get_proxy_config()
    
    if proxy_config:
        print(f"\n✅ Configuration proxy générée:")
        print(f"   Server: {proxy_config['server']}")
        print(f"   Username: {proxy_config['username']}")
        print(f"   Password: {'*' * len(proxy_config['password'])}")
        return proxy_config
    else:
        print("\n❌ Proxy désactivé (configuration incomplète)")
        return None

def test_proxy_connection(proxy_config):
    """Tester la connexion via le proxy"""
    print("\n" + "=" * 60)
    print("🌐 TEST DE CONNEXION VIA PROXY")
    print("=" * 60)
    
    if not proxy_config:
        print("❌ Impossible de tester sans configuration proxy")
        return False
    
    try:
        with sync_playwright() as p:
            print("\n🚀 Lancement du navigateur avec proxy...")
            
            browser = p.chromium.launch(
                headless=False,  # Mode visible pour voir ce qui se passe
                proxy=proxy_config
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0'
            )
            
            page = context.new_page()
            
            print("🔍 Test 1: Vérification de l'IP via ipify.org...")
            try:
                page.goto('https://api.ipify.org?format=json', timeout=30000)
                content = page.content()
                print(f"   Réponse: {content}")
                
                # Extraire l'IP
                import json
                import re
                match = re.search(r'"ip":"([^"]+)"', content)
                if match:
                    ip = match.group(1)
                    print(f"   ✅ IP détectée: {ip}")
                else:
                    print(f"   ⚠️ IP non trouvée dans la réponse")
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
            
            print("\n🔍 Test 2: Vérification de la géolocalisation via ipapi.co...")
            try:
                page.goto('https://ipapi.co/json/', timeout=30000)
                content = page.content()
                
                # Extraire les infos
                import re
                ip_match = re.search(r'"ip":"([^"]+)"', content)
                country_match = re.search(r'"country_name":"([^"]+)"', content)
                city_match = re.search(r'"city":"([^"]+)"', content)
                
                if ip_match:
                    print(f"   IP: {ip_match.group(1)}")
                if country_match:
                    print(f"   Pays: {country_match.group(1)}")
                if city_match:
                    print(f"   Ville: {city_match.group(1)}")
                    
                print(f"   ✅ Test géolocalisation réussi")
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
            
            print("\n🔍 Test 3: Accès à LinkedIn...")
            try:
                page.goto('https://www.linkedin.com', timeout=30000)
                print(f"   URL finale: {page.url}")
                
                if 'linkedin.com' in page.url:
                    print(f"   ✅ Accès à LinkedIn réussi via proxy")
                else:
                    print(f"   ⚠️ Redirection inattendue")
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
            
            print("\n⏳ Fermeture dans 5 secondes...")
            page.wait_for_timeout(5000)
            
            browser.close()
            
            print("\n✅ Tests terminés avec succès")
            return True
            
    except Exception as e:
        print(f"\n❌ Erreur lors du test de connexion: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale"""
    print("\n🧪 SCRIPT DE TEST PROXY LINKEDIN MVP")
    print("=" * 60)
    
    # Test 1: Configuration
    proxy_config = test_proxy_config()
    
    if not proxy_config:
        print("\n❌ Impossible de continuer sans configuration proxy valide")
        print("\n💡 Vérifiez votre fichier .env:")
        print("   - PROXY_URL=geo.iproyal.com")
        print("   - PROXY_USERNAME=...")
        print("   - PROXY_PASSWORD=...")
        print("   - PORT=11200")
        sys.exit(1)
    
    # Test 2: Connexion
    success = test_proxy_connection(proxy_config)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ TOUS LES TESTS SONT PASSÉS")
        print("=" * 60)
        print("\n💡 Le proxy est correctement configuré et fonctionnel!")
        print("   Vous pouvez maintenant l'utiliser avec votre bot LinkedIn.")
    else:
        print("\n" + "=" * 60)
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("=" * 60)
        print("\n💡 Vérifiez:")
        print("   1. Que vos credentials proxy sont corrects")
        print("   2. Que le proxy est actif et accessible")
        print("   3. Que vous avez une connexion internet")

if __name__ == "__main__":
    main()
