"""
Script pour enrichir les prospects via Apify
Usage: python enrich_prospects.py --limit 100
"""
import argparse
from database import SessionLocal, Prospect
from services.apify_enrichment import ApifyEnricher
import json
import re

def clean_handle(url):
    """Extraire l'identifiant unique de l'URL LinkedIn"""
    if not url: return ""
    try:
        # Garder la partie après /in/
        if '/in/' in url:
            path = url.split('/in/')[-1]
        else:
            return "" # URL invalide ou format société
            
        # Nettoyer query params et slashes
        path = path.split('?')[0].strip('/')
        
        # Gérer les suffixes de langue ex: "arthur-mensch/en" -> "arthur-mensch"
        parts = path.split('/')
        handle = parts[0]
        
        # Nettoyage supplémentaire si besoin (certains scrapers ajoutent des IDs)
        return handle.lower()
    except:
        return ""

def enrich_prospects(limit=20, force_clean=False, redo_empty=False):
    db = SessionLocal()
    
    query = db.query(Prospect)
    
    if force_clean:
        print("🧹 Mode nettoyage activé : Ciblage des noms avec '/'")
        prospects = query.filter(Prospect.full_name.like('%/%')).limit(limit).all()
    elif redo_empty:
        print("🔄 Mode Réparation : Ciblage des enrichis MAIS vides")
        # On cible ceux qui sont marqués enrichis mais n'ont pas de résumé ni expériences
        prospects = query.filter(
            Prospect.is_enriched == True,
            (Prospect.summary == None) | (Prospect.summary == ""),
            (Prospect.experiences == None) | (Prospect.experiences == "[]")
        ).limit(limit).all()
    else:
        prospects = query.filter(
            Prospect.is_enriched == False,
            Prospect.linkedin_url != None
        ).limit(limit).all()
    
    if not prospects:
        print("✅ Aucun prospect à traiter.")
        db.close()
        return

    print(f"🎯 {len(prospects)} prospects à traiter...")
    
    # Nettoyage des URLs avant envoi à Apify (CRUCIAL pour éviter les 404)
    clean_urls = []
    for p in prospects:
        u = p.linkedin_url.split('?')[0].rstrip('/')
        parts = u.split('/')
        if len(parts) > 0 and len(parts[-1]) <= 2: # ex: /fr, /en
            u = '/'.join(parts[:-1]) # On garde tout sauf le dernier segment
        clean_urls.append(u)
        
    # Appel Apify avec URLs propres
    enricher = ApifyEnricher()
    try:
        results = enricher.enrich_profiles(clean_urls)
    except Exception as e:
        print(f"❌ Erreur critique Apify: {e}")
        db.close()
        return
    
    # ... (Reste du code identique jusqu'au nettoyage nom)
    # On met à jour le map pour matcher avec les URLs propres
    prospect_map = {}
    for p in prospects:
        # On calcule le handle attendu depuis l'URL propre du prospect
        u = p.linkedin_url.split('?')[0].rstrip('/')
        parts = u.split('/')
        if len(parts) > 0 and len(parts[-1]) <= 2:
            u = '/'.join(parts[:-1])
        h = clean_handle(u)
        if h:
            prospect_map[h] = p

    updated_count = 0
    for item in results:
        apify_url = item.get('url') or item.get('linkedinUrl')
        if not apify_url: continue
        
        handle = clean_handle(apify_url)
        matched_prospect = prospect_map.get(handle)
        
        # Fallback search
        if not matched_prospect:
            for p in prospects:
                h = clean_handle(p.linkedin_url) # Handle de base
                if h and (h in handle or handle in h):
                    matched_prospect = p
                    break
        
        if matched_prospect:
            data = enricher.parse_result_to_db(item)
            
            # Update fields
            matched_prospect.summary = data['summary']
            if data['email']: matched_prospect.email = data['email']
            matched_prospect.phone = data['phone']
            matched_prospect.location = data['location']
            if data['profile_picture']: matched_prospect.profile_picture = data['profile_picture']
            if data['headline']: matched_prospect.headline = data['headline']
            
            matched_prospect.skills = data['skills']
            matched_prospect.experiences = data['experiences']
            matched_prospect.education = data['education']
            matched_prospect.languages = data['languages']
            
            # Check for Ghost/Invalid Profile
            # Criteria: No first name AND no last name, or explicit error in raw data
            if not first and not last:
                print(f"👻 Ghost Profile Detected for {matched_prospect.linkedin_url} (No Name). Deleting...")
                try:
                    # Generic deletion of related actions is handled by Foreign Key cascade if set, 
                    # but we'll stick to simple deletion of the prospect for now.
                    # If you have Actions separately linked, you might need to delete them first if no CASCADE.
                    # Assuming basic deletion is fine or SQLAlchemy handles cascade if configured.
                    session.delete(matched_prospect)
                    session.commit()
                    print(f"🗑️ Deleted Ghost Profile: {matched_prospect.id}")
                except Exception as e:
                    print(f"❌ Error deleting ghost profile: {e}")
                    session.rollback()
                continue

            # Nouveaux champs enrichis
            matched_prospect.connections_count = data['connections_count']
            matched_prospect.followers_count = data['followers_count']
            matched_prospect.is_premium = data['is_premium']
            matched_prospect.is_creator = data['is_creator']
            matched_prospect.is_verified = data['is_verified']
            matched_prospect.years_of_experience = data['years_of_experience']
            
            # Company Details
            matched_prospect.company_size = data['company_size']
            matched_prospect.industry = data['industry']
            
            # RAW
            matched_prospect.raw_data = data['raw_data']
            
            if first and last:
                matched_prospect.full_name = f"{first} {last}"
            elif full:
                matched_prospect.full_name = full
            
            # Clean heuristique
            if matched_prospect.full_name and '/' in matched_prospect.full_name:
                matched_prospect.full_name = matched_prospect.full_name.split('/')[0].strip()

            matched_prospect.is_enriched = True
            updated_count += 1
            print(f"✅ Réparé: {matched_prospect.full_name}")
            
    db.commit()
    db.close()
    print(f"\n🏁 Terminé: {updated_count}/{len(prospects)} réparés.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=20)
    parser.add_argument('--clean', action='store_true')
    parser.add_argument('--redo-empty', action='store_true', help='Relancer ceux qui sont vides')
    args = parser.parse_args()
    
    enrich_prospects(limit=args.limit, force_clean=args.clean, redo_empty=args.redo_empty)
