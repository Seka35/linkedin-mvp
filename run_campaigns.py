"""
Script d'automatisation des campagnes LinkedIn
Lance ce script via cron job pour automatiser les campagnes

Usage:
    python run_campaigns.py
"""
from dotenv import load_dotenv
load_dotenv()

from database import SessionLocal, Prospect, Campaign, Action, Settings
from services.linkedin_bot import LinkedInBot
from services.ai_service import AIService
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
    # Démarrer le bot avec le contexte du compte associé à la campagne
    account = campaign.account
    proxy_config = None
    proxy_config = None
    if account.proxy_url and account.proxy_enabled:
        proxy_config = {
            'server': account.proxy_url,
            'username': account.proxy_username,
            'password': account.proxy_password
        }

    bot = LinkedInBot(
        li_at_cookie=account.li_at_cookie,
        proxy_config=proxy_config,
        user_agent=account.user_agent,
        headless=True
    )
    try:
        if bot.start():
            print("   ✅ Bot démarré\n")
            account.cookie_status = 'valid'
            db.commit()
        else:
            print("   ❌ Échec démarrage bot (Cookie invalide)")
            account.cookie_status = 'expired'
            db.commit()
            return

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
                print(f"      ❌ Échec (Marqué comme failed)")
                # Mettre à jour le prospect pour ne pas retester à l'infini
                prospect.status = 'failed' 
                prospect.last_action_at = datetime.now()
                
                # Logger l'echec
                action = Action(
                    prospect_id=prospect.id,
                    campaign_id=campaign.id,
                    action_type='connect',
                    status='failed',
                    error_message=f"Bot returned False",
                    executed_at=datetime.now()
                )
                db.add(action)
                db.commit()
            
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
    # Démarrer le bot avec le contexte du compte associé à la campagne
    account = campaign.account
    proxy_config = None
    proxy_config = None
    if account.proxy_url and account.proxy_enabled:
        proxy_config = {
            'server': account.proxy_url,
            'username': account.proxy_username,
            'password': account.proxy_password
        }

    bot = LinkedInBot(
        li_at_cookie=account.li_at_cookie,
        proxy_config=proxy_config,
        user_agent=account.user_agent,
        headless=True
    )
    try:
        if bot.start():
            print("   ✅ Bot démarré\n")
            account.cookie_status = 'valid'
            db.commit()
        else:
            print("   ❌ Échec démarrage bot (Cookie invalide)")
            account.cookie_status = 'expired'
            db.commit()
            return
        
        for i, prospect in enumerate(prospects_to_message, 1):
            print(f"   [{i}/{len(prospects_to_message)}] {prospect.full_name}")
            
            # Personnaliser le message
            if campaign.use_ai_customization:
                print("      ✨ Génération message AI...")
                # Récupérer le prompt système
                # Priorité: Compte > Global
                system_prompt = campaign.account.system_prompt
                
                if not system_prompt:
                    system_prompt_setting = db.query(Settings).filter(Settings.key == 'system_prompt').first()
                    system_prompt = system_prompt_setting.value if system_prompt_setting else None
                
                prospect_data = {
                    'name': prospect.full_name,
                    'headline': prospect.headline,
                    'summary': prospect.summary,
                    'experience': prospect.experiences,
                }
                
                ai_service = AIService()
                message = ai_service.generate_icebreaker(prospect_data, system_prompt)
                
                if message.startswith("Error"):
                     print(f"      ⚠️ Erreur AI, fallback sur template classique: {message}")
                     message = campaign.first_message
                     message = message.replace('{name}', prospect.full_name.split()[0] if prospect.full_name else 'there')
                     message = message.replace('{full_name}', prospect.full_name or '')
                     message = message.replace('{company}', prospect.company or '')
                     message = message.replace('{title}', prospect.headline or '')
            else:
                # Template classique
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
                print(f"      ❌ Échec envoi message")
                # Marquer comme échoué temporairement ou définitivement
                # On met 'failed' pour qu'il sorte de la liste "à messager"
                # Ou on pourrait compter les retries. Pour l'instant: Failed.
                # Mais attention, si on met status='failed', il ne sera plus 'connected', donc on perd l'info qu'il est connecté.
                # On va dire que status reste 'connected' mais on log l'échec? 
                # Non le user veut "failed sur le bouton".
                prospect.status = 'failed_message' 
                prospect.last_action_at = datetime.now()
                
                action = Action(
                    prospect_id=prospect.id,
                    campaign_id=campaign.id,
                    action_type='message',
                    status='failed',
                    error_message="Bot returned False",
                    executed_at=datetime.now()
                )
                db.add(action)
                db.commit()
            
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
