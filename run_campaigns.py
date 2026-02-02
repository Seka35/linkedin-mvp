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
import json
import math
try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Python < 3.9 fallback
    from datetime import timezone as ZoneInfo

# Créer le dossier logs s'il n'existe pas
os.makedirs('logs', exist_ok=True)

def check_working_hours(account) -> bool:
    """Vérifie si l'heure actuelle est dans les horaires de travail du compte"""
    try:
        settings = json.loads(account.security_settings) if account.security_settings else {}
        working_hours = settings.get('working_hours', {})
        
        if not working_hours:
            return True # Pas de restriction par défaut
            
        tz_name = settings.get('timezone', 'Europe/Paris')
        try:
            tz = ZoneInfo(tz_name)
        except:
            tz = ZoneInfo('UTC')
            
        now = datetime.now(tz)
        
        # 1. Vérifier le jour (0=Lundi, 6=Dimanche)
        allowed_days = working_hours.get('days', [0, 1, 2, 3, 4]) # Lun-Ven par défaut
        if now.weekday() not in allowed_days:
            print(f"   ⏸️ Hors horaires (Jour {now.weekday()} non autorisé)")
            return False
            
        # 2. Vérifier l'heure
        start_str = working_hours.get('start', '09:00')
        end_str = working_hours.get('end', '18:00')
        
        current_time = now.strftime('%H:%M')
        
        if start_str <= current_time <= end_str:
            return True
        else:
            print(f"   ⏸️ Hors horaires ({current_time} hors de {start_str}-{end_str})")
            return False
            
    except Exception as e:
        print(f"   ⚠️ Erreur vérification horaires: {e}")
        return True # En cas d'erreur, on autorise (fail open) ou block (fail closed)? Fail open pour l'instant.

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
    # --- LOGIQUE DAILY LIMIT ---
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Compter combien d'actions de ce type ont déjà été faites aujourd'hui pour cette campagne
    actions_today = db.query(Action).filter(
        Action.campaign_id == campaign.id,
        Action.action_type == 'connect',
        Action.executed_at >= today_start
    ).count()
    
    remaining_quota = campaign.daily_limit - actions_today
    
    if remaining_quota <= 0:
        print(f"   🛑 Quota journalier atteint ({actions_today}/{campaign.daily_limit}). Pas de nouvelles connexions.")
        return

    print(f"   Quota restant aujourd'hui : {remaining_quota} (Déjà fait: {actions_today})")

    # --- LOGIQUE DE LISSAGE (PACING) ---
    # Pour éviter de tout faire à 8h du matin, on calcule un rythme horaire
    # Ex: 10 actions sur 10 heures (9h-19h) = 1 action/heure
    
    settings = json.loads(campaign.account.security_settings) if campaign.account.security_settings else {}
    working_hours = settings.get('working_hours', {})
    start_str = working_hours.get('start', '09:00')
    end_str = working_hours.get('end', '18:00')
    
    try:
        fmt = '%H:%M'
        t_start = datetime.strptime(start_str, fmt)
        t_end = datetime.strptime(end_str, fmt)
        total_hours = (t_end - t_start).seconds / 3600
        if total_hours < 1: total_hours = 1
        
        # Utiliser ceil pour arrondir à l'entier SUPÉRIEUR
        # Ex: 10 quota / 6 heures = 1.66 -> 2 actions par heure
        # Cela garantit qu'on atteint le quota (quitte à finir 1h plus tôt)
        target_per_hour = max(1, math.ceil(campaign.daily_limit / total_hours))
        
        # On ne veut pas dépasser :
        # 1. Le quota global restant
        # 2. Le rythme horaire cible (pour laisser du travail aux prochaines heures)
        
        limit_now = min(remaining_quota, target_per_hour)
        print(f"   ⏱️ Rythme calculé : {target_per_hour}/heure (sur {total_hours:.1f}h).")
        print(f"   ➡️ Actions pour cette exécution : {limit_now}")
        
    except Exception as e:
        print(f"   ⚠️ Erreur calcul pacing ({e}), fallback sur tout le quota.")
        limit_now = remaining_quota

    prospects = db.query(Prospect).filter(
        Prospect.status == 'new'
    ).limit(limit_now).all()
    
    if not prospects:
        print("   ℹ️ Aucun prospect 'new' disponible")
        return
    
    print(f"   📋 {len(prospects)} prospect(s) à contacter maintenant")
    
    # Démarrer le bot
    # Démarrer le bot avec le contexte du compte associé à la campagne
    account = campaign.account
    
    # Vérification horaires
    if not check_working_hours(account):
        return

    proxy_config = None
    if account.proxy_url and account.proxy_enabled:
        proxy_config = {
            'server': account.proxy_url,
            'username': account.proxy_username,
            'password': account.proxy_password
        }
    
    # Parse settings
    security_settings = json.loads(account.security_settings) if account.security_settings else {}

    bot = LinkedInBot(
        li_at_cookie=account.li_at_cookie,
        proxy_config=proxy_config,
        user_agent=account.user_agent,
        headless=True,
        security_settings=security_settings
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
    
    
    # --- LOGIQUE DAILY LIMIT (MESSAGES) ---
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Compter combien de messages ont déjà été envoyés aujourd'hui pour cette campagne
    actions_today = db.query(Action).filter(
        Action.campaign_id == campaign.id,
        Action.action_type == 'message',
        Action.executed_at >= today_start
    ).count()
    
    remaining_quota = campaign.daily_limit - actions_today
    
    if remaining_quota <= 0:
        print(f"   🛑 Quota journalier de messages atteint ({actions_today}/{campaign.daily_limit}).")
        return

    print(f"   Quota messages restant aujourd'hui : {remaining_quota} (Déjà fait: {actions_today})")

    # --- LOGIQUE DE LISSAGE (PACING - MESSAGES) ---
    settings = json.loads(campaign.account.security_settings) if campaign.account.security_settings else {}
    working_hours = settings.get('working_hours', {})
    start_str = working_hours.get('start', '09:00')
    end_str = working_hours.get('end', '18:00')
    
    try:
        fmt = '%H:%M'
        t_start = datetime.strptime(start_str, fmt)
        t_end = datetime.strptime(end_str, fmt)
        total_hours = (t_end - t_start).seconds / 3600
        if total_hours < 1: total_hours = 1
        
        target_per_hour = max(1, math.ceil(campaign.daily_limit / total_hours))
        
        limit_now = min(remaining_quota, target_per_hour)
        print(f"   ⏱️ Rythme calculé : {target_per_hour}/heure (sur {total_hours:.1f}h).")
        print(f"   ➡️ Messages pour cette exécution : {limit_now}")
        
    except Exception as e:
        print(f"   ⚠️ Erreur calcul pacing ({e}), fallback sur tout le quota.")
        limit_now = remaining_quota

    # Limiter au limit_now (Pacing)
    prospects_to_message = prospects_to_message[:limit_now]
    
    if not prospects_to_message:
        print("   ℹ️ Aucun prospect à contacter maintenant (Quota horaire atteint ou 0).")
        return
    
    # Démarrer le bot
    # Démarrer le bot avec le contexte du compte associé à la campagne
    account = campaign.account
    
    # Vérification horaires
    if not check_working_hours(account):
        return

    proxy_config = None
    if account.proxy_url and account.proxy_enabled:
        proxy_config = {
            'server': account.proxy_url,
            'username': account.proxy_username,
            'password': account.proxy_password
        }

    # Parse settings
    security_settings = json.loads(account.security_settings) if account.security_settings else {}

    bot = LinkedInBot(
        li_at_cookie=account.li_at_cookie,
        proxy_config=proxy_config,
        user_agent=account.user_agent,
        headless=True,
        security_settings=security_settings
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
