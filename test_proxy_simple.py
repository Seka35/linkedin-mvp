#!/usr/bin/env python3
"""
Script de test simple pour vérifier que le proxy fonctionne
"""
import os
from dotenv import load_dotenv
from services.proxy_manager import ProxyManager
from playwright.sync_api import sync_playwright

# Charger les variables d'environnement
load_dotenv()

def main():
    """Test simple du proxy"""
    print("\n🧪 TEST SIMPLE DU PROXY")
    print("=" * 60)
    
    proxy_manager = ProxyManager()
    proxy_config = proxy_manager.get_proxy_config()
    
    if not proxy_config:
        print("❌ Configuration proxy invalide")
        return
    
    print(f"✅ Configuration proxy: {proxy_config['server']}")
    
    try:
        with sync_playwright() as p:
            print("\n🚀 Lancement du navigateur avec proxy...")
            
            browser = p.chromium.launch(
                headless=False,
                proxy=proxy_config
            )
            
            context = browser.new_context()
            page = context.new_page()
            
            # Test 1: Vérifier l'IP
            print("\n🔍 Test 1: Vérification de votre IP...")
            page.goto('https://api.ipify.org?format=json', timeout=30000)
            import re
            content = page.content()
            match = re.search(r'"ip":"([^"]+)"', content)
            if match:
                print(f"   ✅ IP via proxy: {match.group(1)}")
            
            # Test 2: Google
            print("\n🔍 Test 2: Accès à Google...")
            page.goto('https://www.google.com', timeout=30000)
            print(f"   ✅ Google accessible: {page.url}")
            
            # Test 3: Site de test HTTP
            print("\n🔍 Test 3: Accès à example.com...")
            page.goto('https://example.com', timeout=30000)
            print(f"   ✅ Example.com accessible: {page.url}")
            
            # Test 4: Vérifier la géolocalisation
            print("\n🔍 Test 4: Géolocalisation...")
            page.goto('https://ipapi.co/json/', timeout=30000)
            content = page.content()
            
            ip_match = re.search(r'"ip":"([^"]+)"', content)
            country_match = re.search(r'"country_name":"([^"]+)"', content)
            city_match = re.search(r'"city":"([^"]+)"', content)
            
            if ip_match:
                print(f"   IP: {ip_match.group(1)}")
            if country_match:
                print(f"   Pays: {country_match.group(1)}")
            if city_match:
                print(f"   Ville: {city_match.group(1)}")
            
            print("\n⏳ Fermeture dans 5 secondes...")
            page.wait_for_timeout(5000)
            
            browser.close()
            
            print("\n" + "=" * 60)
            print("✅ PROXY FONCTIONNE CORRECTEMENT !")
            print("=" * 60)
            
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
