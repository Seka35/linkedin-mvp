from services.scraper import LinkedInScraper
from database import init_db
from dotenv import load_dotenv
import os

load_dotenv()

def test_scraping():
    print("🚀 Test du service de scraping...")
    
    # S'assurer que la BDD est prête
    init_db()
    
    scraper = LinkedInScraper()
    
    # Requête de test
    query = "CEO startup Paris"
    print(f"🔎 Recherche pour: '{query}'")
    
    # Lancer recherche
    # Note: Google peut bloquer les requêtes automatisées, on limite à 5 résultats pour le test
    results = scraper.search_prospects(query, max_results=5)
    
    print("\n📋 Résultats:")
    for p in results:
        print(f"- {p['full_name']} ({p['linkedin_url']})")

if __name__ == "__main__":
    test_scraping()
