import os
import json
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

APIFY_API_KEY = os.getenv('APIFY_API_KEY')
# Actor: Mass LinkedIn Profile Scraper with Email (dev_fusion/Linkedin-Profile-Scraper)
ACTOR_ID = "dev_fusion/Linkedin-Profile-Scraper"

class ApifyEnricher:
    def __init__(self):
        self.client = ApifyClient(APIFY_API_KEY)
        
    def enrich_profiles(self, linkedin_urls):
        """
        Enrichit une liste d'URLs LinkedIn via Apify.
        Retourne une liste de dictionnaires avec les données complètes.
        """
        if not linkedin_urls:
            return []
            
        print(f"🚀 [Apify] Lancement du scraping pour {len(linkedin_urls)} profils avec {ACTOR_ID}...")
        
        # Configuration de l'input d'après la documentation (screenshots)
        run_input = {
            "profileUrls": linkedin_urls
        }
        
        try:
            # Lancer l'Actor et attendre la fin (synchrone pour l'instant)
            run = self.client.actor(ACTOR_ID).call(run_input=run_input)
        except Exception as e:
            print(f"\n❌ ERREUR APIFY: {str(e)}")
            raise e
            
        print(f"✅ [Apify] Run terminé (ID: {run['id']})")
        
        # Récupérer les résultats du dataset
        results = []
        for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
            results.append(item)
            
        print(f"📊 [Apify] {len(results)} résultats récupérés.")
        return results

    def parse_result_to_db(self, item):
        """Transforme le JSON Apify au format attendu par notre DB"""
        
        # 1. Récupération des champs de base
        summary = item.get('summary') or item.get('about') or item.get('description')
        email = item.get('email')
        phone = item.get('phone') or item.get('phoneNumber')
        location = item.get('location') or item.get('addressCountry')
        
        profile_pic = item.get('profilePic') or item.get('profilePicHighQuality') or item.get('displayPictureUrl')
        headline = item.get('headline') or item.get('jobTitle')
        
        # 2. Gestion intelligente des Expériences
        experiences = item.get('experiences') or item.get('workHistory') or []
        
        # Si pas de liste d'expériences, on construit celle courante depuis la racine
        if not experiences and (item.get('jobTitle') or item.get('companyName')):
            experiences = [{
                'title': item.get('jobTitle'),
                'company': item.get('companyName'),
                'dateRange': item.get('currentJobDuration') or 'Present',
                'location': item.get('jobLocation'),
                'description': 'Poste actuel détecté via profil simplifié'
            }]

        # 3. Gestion de l'Éducation
        education = item.get('education') or item.get('schools') or []
        
        # 4. Compétences
        skills = item.get('skills') or item.get('topSkillsByEndorsements') or []

        return {
            'summary': summary,
            'email': email,
            'phone': phone,
            'location': location,
            'profile_picture': profile_pic,
            'headline': headline,
            'skills': json.dumps(skills),
            'experiences': json.dumps(experiences),
            'education': json.dumps(education),
            'languages': json.dumps(item.get('languages', []))
        }

if __name__ == "__main__":
    # Test unitaire rapide
    enricher = ApifyEnricher()
    # URL de test (Bill Gates ou autre profil public pour ne pas griller de crédit inutilement)
    # Mais pour être sûr, on teste avec une vraie URL de ta DB
    pass
