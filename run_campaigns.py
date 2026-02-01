"""
Script d'automatisation des campagnes LinkedIn
Lance ce script via cron job pour automatiser les campagnes

Usage:
    python run_campaigns.py
"""
from dotenv import load_dotenv
load_dotenv()

from database import SessionLocal, Prospect, Campaign, Action
from services.linkedin_bot import LinkedInBot
from datetime import datetime, timedelta
import time
import argparse
import sys
import os

# Créer le dossier logs s'il n'existe pas
os.makedirs('logs', exist_ok=True)

def random_delay(min_seconds=30, max_seconds=120):
    """Délai aléatoire pour éviter la détection"""
    delay = random.uniform(min_seconds, max_seconds)
    print(f"   ⏳ Attente de {delay:.1f}s...", flush=True)
    time.sleep(delay)

def run_campaigns(campaign_id=None):
    """Exécute les campagnes actives"""
    db = SessionLocal()
    
    if campaign_id:
        print(f"🎯 Lancement ciblé de la campagne ID: {campaign_id}")
        campaigns = db.query(Campaign).filter(Campaign.id == campaign_id).all()
    else:
        # Récupérer toutes les campagnes actives
        campaigns = db.query(Campaign).filter(Campaign.status == 'active').all()
    
    if not campaigns:
        print("❌ Aucune campagne trouvée ou active")
        db.close()
        return
    
    print(f"🎯 {len(campaigns)} campagne(s) à traiter\n")
    
    for campaign in campaigns:
        print("=" * 70)
        print(f"📊 Campagne: {campaign.name}")
        print(f"   Requête: {campaign.search_query}")
        print(f"   Limite: {campaign.daily_limit}/jour")
        print(f"   Délai message: {campaign.message_delay_days} jours")
        print("=" * 70)
        
        # Étape 1: Envoyer des connexions aux prospects "new"
        send_connections(db, campaign)
        
        # Étape 2: Envoyer des messages aux prospects connectés depuis X jours
        send_messages(db, campaign)
        
        print()
    
    db.close()
    print("\n✅ Toutes les campagnes ont été traitées")

def send_connections(db, campaign):
    """Envoie des demandes de connexion/follow aux prospects new"""
    print("\n🤝 ÉTAPE 1: Connexions/Follow")
    
    # Récupérer TOUS les prospects "new" (pas juste ceux de la campagne)
    prospects = db.query(Prospect).filter(
        Prospect.status == 'new'
    ).limit(campaign.daily_limit).all()
    
    if not prospects:
        print("   ℹ️ Aucun prospect 'new' disponible")
        
        # TODO: Auto-scraping si pas assez de prospects
        # print(f"   🔍 Lancement du scraping: {campaign.search_query}")
        # scrape_more_prospects(campaign)
        
        return
    
    print(f"   📋 {len(prospects)} prospect(s) à contacter")
    
    # Démarrer le bot
    bot = LinkedInBot(headless=True)
    try:
        bot.start()
        print("   ✅ Bot démarré\n")
        
        for i, prospect in enumerate(prospects, 1):
            print(f"   [{i}/{len(prospects)}] {prospect.full_name}")
            
            # Envoyer connexion/follow
            result = bot.send_connection_request(prospect.linkedin_url, message="")
            
            # Gérer le résultat
            if isinstance(result, tuple):
                success, status_code = result
            else:
                success = result
                status_code = 'connected' if success else 'failed'
            
            if success:
                # Mettre à jour le prospect
                prospect.status = status_code  # 'connected' ou 'followed'
                prospect.campaign_id = campaign.id  # Tag avec la campagne
                prospect.last_action_at = datetime.now()
                
                # Logger l'action
                action = Action(
                    prospect_id=prospect.id,
                    campaign_id=campaign.id,
                    action_type='connect',
                    status='success',
                    error_message=f"Outcome: {status_code}",
                    executed_at=datetime.now()
                )
                db.add(action)
                db.commit()
                
                print(f"      ✅ {status_code}")
            else:
                print(f"      ❌ Échec")
            
            # Délai aléatoire entre chaque action (30-120 secondes)
            if i < len(prospects):
                random_delay(30, 120)
        
    except Exception as e:
        print(f"   ❌ Erreur bot: {e}")
    finally:
        # Fermer le bot
        if hasattr(bot, 'browser') and bot.browser:
            bot.browser.close()
        if hasattr(bot, 'playwright') and bot.playwright:
            bot.playwright.stop()

def send_messages(db, campaign):
    """Envoie des messages aux prospects connectés depuis X jours"""
    print("\n📨 ÉTAPE 2: Messages automatiques")
    
    # Date limite: il y a X jours
    cutoff_date = datetime.now() - timedelta(days=campaign.message_delay_days)
    
    # Récupérer les prospects connectés/followed depuis X jours, sans message
    prospects = db.query(Prospect).filter(
        Prospect.campaign_id == campaign.id,
        Prospect.status.in_(['connected', 'followed']),
        Prospect.last_action_at <= cutoff_date
    ).all()
    
    # Filtrer ceux qui n'ont pas encore reçu de message
    prospects_to_message = []
    for p in prospects:
        has_message = db.query(Action).filter(
            Action.prospect_id == p.id,
            Action.action_type == 'message',
            Action.status == 'success'
        ).first()
        
        if not has_message:
            prospects_to_message.append(p)
    
    if not prospects_to_message:
        print("   ℹ️ Aucun prospect prêt pour un message")
        return
    
    print(f"   📋 {len(prospects_to_message)} prospect(s) à messager")
    
    # Limiter au daily_limit
    prospects_to_message = prospects_to_message[:campaign.daily_limit]
    
    # Démarrer le bot
    bot = LinkedInBot(headless=True)
    try:
        bot.start()
        print("   ✅ Bot démarré\n")
        
        for i, prospect in enumerate(prospects_to_message, 1):
            print(f"   [{i}/{len(prospects_to_message)}] {prospect.full_name}")
            
            # Personnaliser le message
            message = campaign.first_message
            message = message.replace('{name}', prospect.full_name.split()[0] if prospect.full_name else 'there')
            message = message.replace('{full_name}', prospect.full_name or '')
            message = message.replace('{company}', prospect.company or '')
            message = message.replace('{title}', prospect.headline or '')
            
            # Envoyer le message
            success = bot.send_message(prospect.linkedin_url, message)
            
            if success:
                # Mettre à jour le prospect
                prospect.status = 'messaged'
                prospect.last_action_at = datetime.now()
                
                # Logger l'action
                action = Action(
                    prospect_id=prospect.id,
                    campaign_id=campaign.id,
                    action_type='message',
                    message_sent=message,
                    status='success',
                    executed_at=datetime.now()
                )
                db.add(action)
                db.commit()
                
                print(f"      ✅ Message envoyé")
            else:
                print(f"      ❌ Échec")
            
            # Délai aléatoire entre chaque message (60-180 secondes)
            if i < len(prospects_to_message):
                random_delay(60, 180)
        
    except Exception as e:
        print(f"   ❌ Erreur bot: {e}")
    finally:
        # Fermer le bot
        if hasattr(bot, 'browser') and bot.browser:
            bot.browser.close()
        if hasattr(bot, 'playwright') and bot.playwright:
            bot.playwright.stop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='LinkedIn Campaign Runner')
    parser.add_argument('--campaign_id', type=int, help='ID de la campagne à exécuter')
    args = parser.parse_args()

    print("\n🚀 LANCEMENT DES CAMPAGNES LINKEDIN")
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    
    run_campaigns(campaign_id=args.campaign_id)
    
    print(f"\n🏁 Terminé à {datetime.now().strftime('%H:%M:%S')}")
