"""
Service de scraping pour trouver des prospects LinkedIn.
Utilise Google Search avec dorks et Apify pour enrichissement.
"""

import requests
from apify_client import ApifyClient
import os
from typing import List, Dict
from urllib.parse import quote_plus
import time
import random
import re
from database import get_db, Prospect

class LinkedInScraper:
    """Scraper LinkedIn utilisant Google SERP et Apify"""
    
    def __init__(self):
        self.apify_key = os.getenv('APIFY_API_KEY')
        self.apify_client = ApifyClient(self.apify_key) if self.apify_key else None
    
    def google_dork_search(self, query: str, max_results: int = 20) -> List[Dict]:
        """
        Rechercher des profils LinkedIn via Google Dork.
        """
        # Construire le dork LinkedIn
        full_query = f'site:linkedin.com/in/ {query}'
        encoded_query = quote_plus(full_query)
        
        # Si clé SERP_API_KEY présente, utiliser SearchAPI.io (Recommandé)
        serp_api_key = os.getenv('SERP_API_KEY')
        
        if serp_api_key:
            print(f"🚀 Utilisation de SearchAPI.io pour la recherche...")
            url = "https://www.searchapi.io/api/v1/search"
            params = {
                "engine": "google",
                "q": full_query,
                "api_key": serp_api_key,
                "num": max_results
            }
            try:
                response = requests.get(url, params=params, timeout=20)
                response.raise_for_status() # Raise error for 4xx/5xx
                data = response.json()
                
                if "error" in data:
                     raise Exception(data["error"])
                
                linkedin_urls = []
                if "organic_results" in data:
                    for result in data["organic_results"]:
                        link = result.get("link", "")
                        if "linkedin.com/in/" in link:
                            linkedin_urls.append(link)
                
                # Dédupliquer
                unique_urls = list(set(linkedin_urls))[:max_results]
                results = []
                for url in unique_urls:
                    username = url.split('/in/')[-1].rstrip('/')
                    results.append({
                        'linkedin_url': url,
                        'full_name': self._extract_name_from_url(username),
                        'source': 'searchapi_io'
                    })
                
                print(f"✅ Trouvé {len(results)} profils via SearchAPI.io")
                return results

            except Exception as e:
                print(f"❌ Erreur SearchAPI.io: {e}")
                pass
        
        # 2. Backup: SerpAPI (si configuré)
        serp_api_backup_key = os.getenv('SERP_API_BACKUP_KEY')
        if serp_api_backup_key:
             print(f"⚠️ Switch vers SerpAPI (Backup)...")
             try:
                url_serp = "https://serpapi.com/search.json"
                params_serp = {
                    "engine": "google",
                    "q": full_query,
                    "api_key": serp_api_backup_key,
                    "num": max_results
                }
                response = requests.get(url_serp, params=params_serp, timeout=20)
                data = response.json()
                
                if "error" in data:
                    print(f"❌ Erreur SerpAPI: {data['error']}")
                else:
                    linkedin_urls = []
                    if "organic_results" in data:
                        for result in data["organic_results"]:
                            link = result.get("link", "")
                            if "linkedin.com/in/" in link:
                                linkedin_urls.append(link)
                    
                    unique_urls = list(set(linkedin_urls))[:max_results]
                    results = []
                    for url in unique_urls:
                        username = url.split('/in/')[-1].rstrip('/')
                        results.append({
                            'linkedin_url': url,
                            'full_name': self._extract_name_from_url(username),
                            'source': 'serpapi_backup'
                        })
                    
                    if results:
                        print(f"✅ Trouvé {len(results)} profils via SerpAPI (Backup)")
                        return results
                    else:
                        print("⚠️ SerpAPI: Aucun résultat trouvé")

             except Exception as e:
                 print(f"❌ Erreur SerpAPI Backup: {e}")

        # Fallback: DuckDuckGo HTML (plus permissif)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
            'Referer': 'https://html.duckduckgo.com/'
        }
        
        try:
            print(f"🔍 Recherche Google: {full_query}")
            response = requests.get(url, headers=headers, timeout=10)
            
            # Parser les résultats (simple regex pour MVP)
            # Regex améliorée pour capturer proprement les URLs
            linkedin_urls = re.findall(r'https://www\.linkedin\.com/in/[\w-]+', response.text)
            
            # Dédupliquer
            unique_urls = list(set(linkedin_urls))[:max_results]
            
            results = []
            for url in unique_urls:
                # Extraire username du profil
                username = url.split('/in/')[-1].rstrip('/')
                
                results.append({
                    'linkedin_url': url,
                    'full_name': self._extract_name_from_url(username),
                    'source': 'google_serp'
                })
            
            print(f"✅ Trouvé {len(results)} profils via DuckDuckGo")
            return results
            
        except Exception as e:
            print(f"❌ Erreur DDG Search: {e}")
            return []
    
    def apify_search(self, search_url: str, max_results: int = 20) -> List[Dict]:
        """
        Utiliser Apify pour scraper LinkedIn Sales Navigator ou profils.
        """
        if not self.apify_client:
            print("⚠️ Apify non configuré")
            return []
        
        try:
            # Utiliser l'actor Apify LinkedIn Scraper
            # https://apify.com/apify/linkedin-profile-scraper
            
            run_input = {
                "startUrls": [{"url": search_url}],
                "maxResults": max_results,
            }
            
            print(f"🔄 Lancement Apify scraping...")
            run = self.apify_client.actor("apify/linkedin-profile-scraper").call(run_input=run_input)
            
            results = []
            for item in self.apify_client.dataset(run["defaultDatasetId"]).iterate_items():
                results.append({
                    'linkedin_url': item.get('url'),
                    'full_name': item.get('fullName'),
                    'headline': item.get('headline'),
                    'company': item.get('company'),
                    'location': item.get('location'),
                    'profile_picture': item.get('photoUrl'),
                    'source': 'apify'
                })
            
            print(f"✅ Apify a trouvé {len(results)} profils")
            return results
            
        except Exception as e:
            print(f"❌ Erreur Apify: {e}")
            return []
    
    def _extract_name_from_url(self, username: str) -> str:
        """Extraire un nom lisible depuis un username LinkedIn"""
        # Remplacer tirets par espaces et capitaliser
        name = username.replace('-', ' ').title()
        return name
    
    def search_prospects(self, query: str, use_apify: bool = False, max_results: int = 20, account_id: int = None) -> List[Dict]:
        """
        Méthode principale de recherche et sauvegarde.
        """
        results = []
        
        # 1. Google Dork (toujours)
        google_results = self.google_dork_search(query, max_results)
        results.extend(google_results)
        
        # 2. Apify (optionnel)
        if use_apify and self.apify_client:
            # TODO: Implémenter logique spécifique Apify selon besoins
            pass
        
        # 3. Sauvegarder en BDD
        self._save_to_db(results, account_id)
        
        return results

    def _save_to_db(self, prospects_data: List[Dict], account_id: int = None):
        """Sauvegarder les prospects trouvés en base de données"""
        db = next(get_db())
        try:
            count = 0
            for data in prospects_data:
                # Vérifier si existe déjà (Scope Global ou par Compte ?)
                # Pour l'instant, check global par URL pour éviter doublons, 
                # OU check par compte si on veut autoriser le même prospect sur plusieurs comptes.
                # ACTUELLEMENT: check global par linkedin_url (car pas de composite unique constraint facile en SQLite sans migration complexe)
                # FIX: Check si existe DANS CE COMPTE
                
                query = db.query(Prospect).filter(Prospect.linkedin_url == data['linkedin_url'])
                if account_id:
                    query = query.filter(Prospect.account_id == account_id)
                
                existing = query.first()
                
                if not existing:
                    prospect = Prospect(
                        linkedin_url=data['linkedin_url'],
                        full_name=data.get('full_name'),
                        headline=data.get('headline'),
                        company=data.get('company'),
                        location=data.get('location'),
                        profile_picture=data.get('profile_picture'),
                        source=data.get('source', 'manual'),
                        status='new',
                        account_id=account_id
                    )
                    db.add(prospect)
                    count += 1
            
            db.commit()
            if count > 0:
                print(f"💾 {count} nouveaux prospects sauvegardés en BDD (Account {account_id})")
            else:
                print("💾 Aucun nouveau prospect à sauvegarder (doublons)")
                
        except Exception as e:
            print(f"❌ Erreur sauvegarde BDD: {e}")
            db.rollback()
        finally:
            db.close()
