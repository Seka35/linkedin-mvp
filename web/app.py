"""
Application Flask pour l'interface web du bot LinkedIn.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import sys
import os

# Ajouter le dossier parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import init_db, SessionLocal, Prospect, Campaign, Action, Settings
from services.scraper import LinkedInScraper
from services.linkedin_bot import LinkedInBot
from services.ai_service import AIService
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

# Filtre pour parser le JSON dans les templates
import json
@app.template_filter('from_json')
def from_json_filter(value):
    if not value:
        return []
    try:
        if isinstance(value, str):
            return json.loads(value)
        return value
    except:
        return []

# Initialiser la DB au démarrage (déjà fait dans main.py mais utile si lancé seul)
# init_db()

# Instance globale du scraper
scraper = LinkedInScraper()

# Instance globale du bot (sera initialisée à la demande)
bot = None

from sqlalchemy.orm import joinedload

@app.route('/')
def index():
    """Page d'accueil avec stats"""
    db = SessionLocal()
    
    total_prospects = db.query(Prospect).count()
    new_prospects = db.query(Prospect).filter(Prospect.status == 'new').count()
    connected = db.query(Prospect).filter(Prospect.status == 'connected').count()
    followed = db.query(Prospect).filter(Prospect.status == 'followed').count()
    messaged = db.query(Action).filter(Action.action_type == 'message', Action.status == 'success').distinct(Action.prospect_id).count()
    
    # Eager load 'prospect' to avoid DetachedInstanceError after db.close()
    recent_actions = db.query(Action).options(joinedload(Action.prospect)).order_by(Action.executed_at.desc()).limit(10).all()
    
    db.close()
    
    stats = {
        'total_prospects': total_prospects,
        'new_prospects': new_prospects,
        'connected': connected,
        'followed': followed,
        'messaged': messaged,
    }
    
    return render_template('index.html', stats=stats, recent_actions=recent_actions)

@app.route('/prospects')
def prospects():
    """Page liste des prospects"""
    db = SessionLocal()
    
    status_filter = request.args.get('status', 'all')
    
    # Filtrage spécial pour "messaged" : tous ceux qui ont reçu au moins 1 message
    if status_filter == 'messaged':
        # Récupérer les IDs des prospects qui ont reçu au moins 1 message
        prospect_ids_with_messages = db.query(Action.prospect_id).filter(
            Action.action_type == 'message',
            Action.status == 'success'
        ).distinct().all()
        
        prospect_ids = [pid[0] for pid in prospect_ids_with_messages]
        
        if prospect_ids:
            prospects_list = db.query(Prospect).filter(
                Prospect.id.in_(prospect_ids)
            ).order_by(Prospect.added_at.desc()).all()
        else:
            prospects_list = []
    else:
        # Filtrage normal par statut
        query = db.query(Prospect)
        if status_filter != 'all':
            query = query.filter(Prospect.status == status_filter)
        prospects_list = query.order_by(Prospect.added_at.desc()).all()
    
    # Pour chaque prospect, compter le nombre de messages envoyés
    for prospect in prospects_list:
        message_count = db.query(Action).filter(
            Action.prospect_id == prospect.id,
            Action.action_type == 'message',
            Action.status == 'success'
        ).count()
        prospect.message_count = message_count
    
    # Calculer les compteurs pour chaque filtre
    counts = {
        'all': db.query(Prospect).count(),
        'new': db.query(Prospect).filter(Prospect.status == 'new').count(),
        'connected': db.query(Prospect).filter(Prospect.status == 'connected').count(),
        'followed': db.query(Prospect).filter(Prospect.status == 'followed').count(),
        'messaged': db.query(Action).filter(
            Action.action_type == 'message',
            Action.status == 'success'
        ).distinct(Action.prospect_id).count()
    }

    # Préparer les données pour la modale JS (sérialisation propre)
    import json
    prospects_data = {}
    for p in prospects_list:
        prospects_data[str(p.id)] = {
            'name': p.full_name,
            'headline': p.headline or '',
            'location': p.location or '',
            'photo': p.profile_picture or '',
            'about': p.summary or 'No description available.',
            'experience': p.experiences or 'No experience info.',
            'skills': p.skills or ''
        }
    
    db.close()
    
    return render_template('prospects.html', 
                         prospects=prospects_list, 
                         status_filter=status_filter, 
                         counts=counts,
                         prospects_json=json.dumps(prospects_data))

@app.route('/campaigns')
def campaigns():
    """Page liste des campagnes"""
    db = SessionLocal()
    
    campaigns_list = db.query(Campaign).order_by(Campaign.created_at.desc()).all()
    
    # Calculer les stats pour chaque campagne
    for campaign in campaigns_list:
        # Nombre de prospects associés à cette campagne
        campaign.stats_prospects = db.query(Prospect).filter(Prospect.campaign_id == campaign.id).count()
        
        # Nombre de connexions envoyées (basé sur les logs actions)
        campaign.stats_connected = db.query(Action).filter(
            Action.campaign_id == campaign.id,
            Action.action_type == 'connect', 
            Action.status == 'success'
        ).count()
        
        # Nombre de messages envoyés
        campaign.stats_messaged = db.query(Action).filter(
            Action.campaign_id == campaign.id,
            Action.action_type == 'message',
            Action.status == 'success'
        ).count()

    db.close()
    
    return render_template('campaigns.html', campaigns=campaigns_list)

@app.route('/messages')
def messages():
    """Page liste des messages envoyés"""
    db = SessionLocal()
    
    # Récupérer toutes les actions de type 'message' avec eager loading du prospect
    messages_list = db.query(Action).options(joinedload(Action.prospect)).filter(
        Action.action_type == 'message'
    ).order_by(Action.executed_at.desc()).all()
    
    # Extraire les prospects uniques pour les modales
    unique_prospects = {action.prospect for action in messages_list if action.prospect}
    
    db.close()
    
    return render_template('messages.html', messages=messages_list, unique_prospects=unique_prospects)

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    """API: Lancer un scraping"""
    data = request.json
    query = data.get('query')
    max_results = int(data.get('max_results', 20))
    use_apify = data.get('use_apify', False)
    
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    # Scraper
    print(f"🌍 API Scrape request: {query}")
    results = scraper.search_prospects(query, use_apify, max_results)
    
    # Sauvegarder en DB (déjà géré dans search_prospects, mais utile pour stats retour)
    # On sait que scraper.search_prospects retourne la liste trouvée et sauvegarde.
    
    # Enrichissement automatique
    try:
        # Import local pour éviter les problèmes cirk
        import sys
        import os
        sys.path.append(os.getcwd()) # Assurer que le CWD est dans le path
        from enrich_prospects import enrich_prospects as run_enrichment
        
        print(f"🚀 Lancement enrichissement automatique pour {len(results)} prospects...")
        # On lance l'enrichissement pour le nombre de résultats trouvés
        run_enrichment(limit=len(results), force_clean=False)
    except Exception as e:
        print(f"⚠️ Erreur enrichissement auto: {e}")

    return jsonify({
        'success': True,
        'found': len(results),
        # 'added': ... (serait mieux si search_prospects le retournait)
        'added': len(results) # Une approximation pour le MVP
    })

@app.route('/api/connect', methods=['POST'])
def api_connect():
    """API: Envoyer demande de connexion"""
    data = request.json
    prospect_id = data.get('prospect_id')
    message = data.get('message', '')
    
    db = SessionLocal()
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    
    if not prospect:
        db.close()
        return jsonify({'error': 'Prospect not found'}), 404
    
    # TOUJOURS démarrer un bot FRAIS
    print("🔄 Démarrage d'une session bot fraîche...")
    fresh_bot = None
    try:
        fresh_bot = LinkedInBot(headless=False)
        fresh_bot.start()
        
        # Envoyer demande de connexion
        result = fresh_bot.send_connection_request(prospect.linkedin_url, message)
        
        # Gérer le retour (Tuple ou Bool)
        if isinstance(result, tuple):
            success, status_code = result
        else:
            success = result
            status_code = 'connected' if success else 'failed'
            
    except Exception as e:
        print(f"❌ Erreur bot: {e}")
        success = False
        status_code = 'failed'
    finally:
        # Toujours fermer le bot après utilisation
        if fresh_bot:
            try:
                if hasattr(fresh_bot, 'browser') and fresh_bot.browser:
                    fresh_bot.browser.close()
                if hasattr(fresh_bot, 'playwright') and fresh_bot.playwright:
                    fresh_bot.playwright.stop()
            except:
                pass
    
    # Logger l'action
    action = Action(
        prospect_id=prospect.id,
        action_type='connect',
        message_sent=message,
        status='success' if success else 'failed',
        error_message=f"Outcome: {status_code}" # On note le résultat (followed/connected) ici
    )
    db.add(action)
    
    # Mettre à jour prospect
    if success:
        if status_code == 'followed':
            prospect.status = 'followed'
        else:
            prospect.status = 'connected'
            
        prospect.last_action_at = datetime.utcnow()
    
    db.commit()
    db.close()
    
    return jsonify({'success': success})

@app.route('/api/message', methods=['POST'])
def api_message():
    """API: Envoyer un message"""
    data = request.json
    prospect_id = data.get('prospect_id')
    message = data.get('message')
    
    db = SessionLocal()
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    
    if not prospect:
        db.close()
        return jsonify({'error': 'Prospect not found'}), 404
    
    # TOUJOURS démarrer un bot FRAIS pour éviter les sessions corrompues
    print("🔄 Démarrage d'une session bot fraîche...")
    fresh_bot = None
    try:
        fresh_bot = LinkedInBot(headless=False)
        fresh_bot.start()
        
        # Envoyer message
        success = fresh_bot.send_message(prospect.linkedin_url, message)
        
    except Exception as e:
        print(f"❌ Erreur bot: {e}")
        success = False
    finally:
        # Toujours fermer le bot après utilisation
        if fresh_bot:
            try:
                if hasattr(fresh_bot, 'browser') and fresh_bot.browser:
                    fresh_bot.browser.close()
                if hasattr(fresh_bot, 'playwright') and fresh_bot.playwright:
                    fresh_bot.playwright.stop()
            except:
                pass
    
    # Logger l'action
    action = Action(
        prospect_id=prospect.id,
        action_type='message',
        message_sent=message,
        status='success' if success else 'failed'
    )
    db.add(action)
    
    # Mettre à jour prospect
    if success:
        prospect.status = 'messaged'
        prospect.last_action_at = datetime.utcnow()
    
    db.commit()
    db.close()
    
    return jsonify({'success': success})

@app.route('/api/campaign/create', methods=['POST'])
def api_create_campaign():
    """API: Créer une nouvelle campagne"""
    data = request.json
    
    db = SessionLocal()
    
    campaign = Campaign(
        name=data.get('name'),
        search_query=data.get('search_query'),
        connection_message=data.get('connection_message'),
        first_message=data.get('first_message'),
        message_delay_days=data.get('message_delay_days', 3),
        daily_limit=data.get('daily_limit', 10),
        use_ai_customization=data.get('use_ai_customization', False)
    )
    
    db.add(campaign)
    db.commit()
    
    campaign_id = campaign.id
    db.close()
    
    return jsonify({'success': True, 'campaign_id': campaign_id})



@app.route('/api/campaign/run', methods=['POST'])
def api_run_campaign():
    """API: Lancer une campagne manuellement"""
    import subprocess
    import threading
    
    data = request.json
    campaign_id = data.get('campaign_id')
    
    db = SessionLocal()
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    
    if not campaign:
        db.close()
        return jsonify({'success': False, 'error': 'Campagne introuvable'})
    
    if campaign.status != 'active':
        db.close()
        return jsonify({'success': False, 'error': 'La campagne doit être active'})
    
    db.close()
    
    # Créer le dossier logs
    import os
    os.makedirs('logs', exist_ok=True)
    
    # Lancer run_campaigns.py en arrière-plan avec redirection logs
    def run_script():
        log_file_path = f'logs/campaign_{campaign_id}.log'
        with open(log_file_path, 'w') as log_file:
            # -u pour unbuffered output (très important pour le temps réel)
            subprocess.run(
                ['./venv/bin/python', '-u', 'run_campaigns.py', '--campaign_id', str(campaign_id)], 
                cwd='/home/seka/Desktop/linkedin-mvp',
                stdout=log_file,
                stderr=subprocess.STDOUT
            )
    
    thread = threading.Thread(target=run_script)
    thread.start()
    
    return jsonify({'success': True, 'message': 'Campagne lancée en arrière-plan'})

@app.route('/api/campaign/logs/<int:campaign_id>')
def api_campaign_logs(campaign_id):
    """API: Lire les logs d'une campagne"""
    log_file_path = f'logs/campaign_{campaign_id}.log'
    
    if not os.path.exists(log_file_path):
        return jsonify({'logs': 'En attente de démarrage...'})
        
    try:
        with open(log_file_path, 'r') as f:
            content = f.read()
        return jsonify({'logs': content})
    except Exception as e:
        return jsonify({'logs': f'Erreur lecture logs: {str(e)}'})

@app.route('/api/campaign/pause', methods=['POST'])
def api_pause_campaign():
    """API: Mettre en pause une campagne"""
    data = request.json
    campaign_id = data.get('campaign_id')
    
    db = SessionLocal()
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    
    if campaign:
        campaign.status = 'paused'
        db.commit()
    
    db.close()
    
    return jsonify({'success': True})

@app.route('/api/campaign/resume', methods=['POST'])
def api_resume_campaign():
    """API: Reprendre une campagne"""
    data = request.json
    campaign_id = data.get('campaign_id')
    
    db = SessionLocal()
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    
    if campaign:
        campaign.status = 'active'
        db.commit()
    
    db.close()
    
    return jsonify({'success': True})


@app.route('/api/prospects/<int:prospect_id>', methods=['GET', 'DELETE'])
def api_prospect_item(prospect_id):
    db = SessionLocal()
    prospect = db.query(Prospect).get(prospect_id)
    
    if not prospect:
        db.close()
        return jsonify({'success': False, 'error': 'Not found'}), 404

    if request.method == 'GET':
        # Retourner les détails pour la modale
        data = {
            'id': prospect.id,
            'name': prospect.full_name,
            'headline': prospect.headline or '',
            'location': prospect.location or '',
            'photo': prospect.profile_picture or '',
            'about': prospect.summary or '',
            'email': prospect.email or '',
            'phone': prospect.phone or '',
            'experience': prospect.experiences or '',
            'skills': prospect.skills or ''
        }
        db.close()
        return jsonify({'success': True, 'prospect': data})

    if request.method == 'DELETE':
        try:
            # Supprimer aussi les actions liées
            db.query(Action).filter(Action.prospect_id == prospect.id).delete()
            db.delete(prospect)
            db.commit()
            db.close()
            return jsonify({'success': True})
        except Exception as e:
            db.rollback()
            db.close()
            return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/campaigns/<int:campaign_id>', methods=['DELETE'])
def delete_campaign(campaign_id):
    """API: Supprimer une campagne"""
    db = SessionLocal()
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    
    if not campaign:
        db.close()
        return jsonify({'error': 'Campaign not found'}), 404
        
    try:
        db.delete(campaign)
        db.commit()
        success = True
    except Exception as e:
        print(f"❌ Erreur suppression campagne: {e}")
        db.rollback()
        success = False
    finally:
        db.close()
        
    return jsonify({'success': success})

@app.route('/api/ai/generate', methods=['POST'])
def api_ai_generate():
    """API: Générer un message avec l'IA"""
    data = request.json
    prospect_id = data.get('prospect_id')
    prompt_override = data.get('prompt')

    db = SessionLocal()
    prospect = db.query(Prospect).get(prospect_id)
    
    if not prospect:
        db.close()
        return jsonify({'success': False, 'error': 'Prospect not found'}), 404

    # Récupérer le prompt système depuis les settings si pas d'override
    if not prompt_override:
        setting = db.query(Settings).filter(Settings.key == 'system_prompt').first()
        if setting:
            prompt_override = setting.value

    db.close()

    # Préparer les données pour le service IA
    prospect_data = {
        'name': prospect.full_name,
        'headline': prospect.headline,
        'summary': prospect.summary,
        'experience': prospect.experiences,
    }

    ai_service = AIService()
    generated_message = ai_service.generate_icebreaker(prospect_data, prompt_override)

    if generated_message.startswith("Error"):
        return jsonify({'success': False, 'error': generated_message}), 500

    return jsonify({'success': True, 'message': generated_message})

@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    """Page de configuration (Prompts, etc)"""
    db = SessionLocal()

    if request.method == 'POST':
        # Sauvegarde
        system_prompt = request.form.get('system_prompt')
        
        # Upsert
        setting = db.query(Settings).filter(Settings.key == 'system_prompt').first()
        if not setting:
            setting = Settings(key='system_prompt')
            db.add(setting)
        
        setting.value = system_prompt
        db.commit()
        db.close()
        return redirect(url_for('settings_page', saved=1))

    # Lecture
    setting = db.query(Settings).filter(Settings.key == 'system_prompt').first()
    current_prompt = setting.value if setting else ""
    # Default prompt if empty
    from services.ai_service import DEFAULT_PROMPT
    if not current_prompt:
        current_prompt = DEFAULT_PROMPT.strip()

    db.close()
    return render_template('settings.html', system_prompt=current_prompt, saved=request.args.get('saved'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
