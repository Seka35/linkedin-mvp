#!/usr/bin/env python3
"""
Test final du proxy avec LinkedIn (sans authentification)
"""
import os
from dotenv import load_dotenv
from services.proxy_manager import ProxyManager
from playwright.sync_api import sync_playwright

load_dotenv()

def main():
    print("\n🧪 TEST PROXY AVEC LINKEDIN")
    print("=" * 60)
    
    proxy_manager = ProxyManager()
    proxy_config = proxy_manager.get_proxy_config()
    
    if not proxy_config:
        print("❌ Configuration proxy invalide")
        return
    
    print(f"✅ Proxy configuré: {proxy_config['server']}")
    print(f"   Username: {proxy_config['username']}")
    print(f"   Password: {'*' * len(proxy_config['password'])}")
    
    try:
        with sync_playwright() as p:
            print("\n🚀 Lancement du navigateur avec proxy...")
            
            browser = p.chromium.launch(
                headless=False,
                proxy=proxy_config
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0'
            )
            
            page = context.new_page()
            
            # Test 1: Vérifier l'IP
            print("\n🔍 Test 1: Vérification de votre IP...")
            try:
                page.goto('https://api.ipify.org?format=json', timeout=30000)
                import re
                content = page.content()
                match = re.search(r'"ip":"([^"]+)"', content)
                if match:
                    print(f"   ✅ IP via proxy: {match.group(1)}")
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
            
            # Test 2: LinkedIn
            print("\n🔍 Test 2: Accès à LinkedIn...")
            try:
                page.goto('https://www.linkedin.com', timeout=30000)
                page.wait_for_timeout(3000)
                
                current_url = page.url
                print(f"   URL actuelle: {current_url}")
                
                if 'linkedin.com' in current_url:
                    print(f"   ✅ LinkedIn accessible via proxy!")
                    
                    # Vérifier si on est redirigé vers login
                    if '/login' in current_url or 'authwall' in current_url:
                        print(f"   ℹ️  Page de login détectée (normal sans cookie)")
                    elif '/feed' in current_url:
                        print(f"   ✅ Feed détecté (vous êtes connecté!)")
                    else:
                        print(f"   ℹ️  Page d'accueil LinkedIn")
                else:
                    print(f"   ⚠️  Redirection inattendue")
                    
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
            
            print("\n⏳ Gardez le navigateur ouvert 10 secondes pour vérifier...")
            page.wait_for_timeout(10000)
            
            browser.close()
            
            print("\n" + "=" * 60)
            print("✅ TEST TERMINÉ")
            print("=" * 60)
            print("\n💡 Si vous avez vu LinkedIn s'afficher, le proxy fonctionne!")
            
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
