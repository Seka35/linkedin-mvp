"""
Application Flask pour l'interface web du bot LinkedIn.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import sys
import os
import requests
import bcrypt
from functools import wraps

# Ajouter le dossier parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import init_db, SessionLocal, Prospect, Campaign, Action, Settings, Account
from database.models import User
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

from flask import g, session

def login_required(f):
    """Decorator to protect routes - redirect to login if not authenticated"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def load_account():
    """Charger le compte actif pour la requête"""
    # Skip authentication check for static files and login page
    if request.endpoint and ('static' in request.endpoint or request.endpoint == 'login'):
        return
    
    # Check if user is authenticated
    if 'user_id' not in session and request.endpoint != 'login':
        return redirect(url_for('login'))
        
    db = SessionLocal()
    account_id = session.get('account_id')
    
    if account_id:
        g.account = db.query(Account).get(account_id)
    
    # Si pas de compte en session ou compte invalide, charger le par défaut (ID 1)
    if not hasattr(g, 'account') or not g.account:
        g.account = db.query(Account).order_by(Account.id).first()
        if g.account:
            session['account_id'] = g.account.id
            
    db.close()

@app.context_processor
def inject_account():
    """Injecter le compte actuel et la liste des comptes dans tous les templates"""
    def get_all_accounts():
        db = SessionLocal()
        accounts = db.query(Account).all()
        db.close()
        return accounts
        
    return dict(current_account=getattr(g, 'account', None), get_all_accounts=get_all_accounts)

from sqlalchemy.orm import joinedload

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db = SessionLocal()
        user = db.query(User).filter(User.username == username).first()
        db.close()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid credentials")
    
    # If already logged in, redirect to index
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Déconnexion"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    """Page d'accueil avec stats"""
    db = SessionLocal()
    
    account_id = g.account.id if g.account else 0
    
    total_prospects = db.query(Prospect).filter(Prospect.account_id == account_id).count()
    new_prospects = db.query(Prospect).filter(Prospect.account_id == account_id, Prospect.status == 'new').count()
    connected = db.query(Prospect).filter(Prospect.account_id == account_id, Prospect.status == 'connected').count()
    followed = db.query(Prospect).filter(Prospect.account_id == account_id, Prospect.status == 'followed').count()
    messaged = db.query(Action).join(Prospect).filter(Prospect.account_id == account_id, Action.action_type == 'message', Action.status == 'success').distinct(Action.prospect_id).count()
    
    # Eager load 'prospect' to avoid DetachedInstanceError after db.close()
    # Eager load 'prospect' to avoid DetachedInstanceError after db.close()
    recent_actions = db.query(Action).join(Prospect).filter(Prospect.account_id == account_id).options(joinedload(Action.prospect)).order_by(Action.executed_at.desc()).limit(10).all()
    
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
        prospect_ids_with_messages = db.query(Action.prospect_id).join(Prospect).filter(
            Prospect.account_id == g.account.id,
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
        query = db.query(Prospect).filter(Prospect.account_id == g.account.id)
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
    account_id = g.account.id
    counts = {
        'all': db.query(Prospect).filter(Prospect.account_id == account_id).count(),
        'new': db.query(Prospect).filter(Prospect.account_id == account_id, Prospect.status == 'new').count(),
        'connected': db.query(Prospect).filter(Prospect.account_id == account_id, Prospect.status == 'connected').count(),
        'followed': db.query(Prospect).filter(Prospect.account_id == account_id, Prospect.status == 'followed').count(),
        'messaged': db.query(Action).join(Prospect).filter(
            Prospect.account_id == account_id,
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
    
    campaigns_list = db.query(Campaign).filter(Campaign.account_id == g.account.id).order_by(Campaign.created_at.desc()).all()
    
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
    # Récupérer toutes les actions de type 'message' avec eager loading du prospect
    messages_list = db.query(Action).join(Prospect).options(joinedload(Action.prospect)).filter(
        Prospect.account_id == g.account.id,
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
    print(f"🌍 API Scrape request: {query} (Account: {g.account.id})")
    results = scraper.search_prospects(query, use_apify, max_results, account_id=g.account.id)
    
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
        # Configuration Proxy depuis le compte
        # Configuration Proxy depuis le compte (seulement si activé)
        proxy_config = None
        if g.account.proxy_url and g.account.proxy_enabled:
            proxy_config = {
                'server': g.account.proxy_url,
                'username': g.account.proxy_username,
                'password': g.account.proxy_password
            }

        fresh_bot = LinkedInBot(
            li_at_cookie=g.account.li_at_cookie, 
            proxy_config=proxy_config,
            user_agent=g.account.user_agent,
            headless=False
        )
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
        # Configuration Proxy depuis le compte
        # Configuration Proxy depuis le compte (seulement si activé)
        proxy_config = None
        if g.account.proxy_url and g.account.proxy_enabled:
            proxy_config = {
                'server': g.account.proxy_url,
                'username': g.account.proxy_username,
                'password': g.account.proxy_password
            }

        fresh_bot = LinkedInBot(
            li_at_cookie=g.account.li_at_cookie,
            proxy_config=proxy_config,
            user_agent=g.account.user_agent,
            headless=False
        )
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
        account_id=g.account.id,
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


@app.route('/api/campaigns/<int:campaign_id>', methods=['GET', 'PUT', 'DELETE'])
def api_campaign_item(campaign_id):
    """API: Gestion unitaire d'une campagne (GET, UPDATE, DELETE)"""
    db = SessionLocal()
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    
    if not campaign:
        db.close()
        return jsonify({'error': 'Campaign not found'}), 404
        
    try:
        if request.method == 'GET':
            data = {
                'id': campaign.id,
                'name': campaign.name,
                'search_query': campaign.search_query,
                'first_message': campaign.first_message,
                'message_delay_days': campaign.message_delay_days,
                'daily_limit': campaign.daily_limit,
                'use_ai_customization': campaign.use_ai_customization
            }
            return jsonify({'success': True, 'campaign': data})

        if request.method == 'PUT':
            data = request.json
            campaign.name = data.get('name', campaign.name)
            campaign.search_query = data.get('search_query', campaign.search_query)
            campaign.first_message = data.get('first_message', campaign.first_message)
            campaign.message_delay_days = int(data.get('message_delay_days', campaign.message_delay_days))
            campaign.daily_limit = int(data.get('daily_limit', campaign.daily_limit))
            campaign.use_ai_customization = data.get('use_ai_customization', campaign.use_ai_customization)
            
            db.commit()
            return jsonify({'success': True})

        if request.method == 'DELETE':
            db.delete(campaign)
            db.commit()
            return jsonify({'success': True})
            
    except Exception as e:
        print(f"❌ Erreur API Campagne: {e}")
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

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

    # Récupérer le prompt système depuis le compte, ou global si vide
    if not prompt_override:
        if hasattr(g, 'account') and g.account and g.account.system_prompt:
             prompt_override = g.account.system_prompt
        
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

    # Récupérer tous les comptes pour l'affichage dans Settings
    accounts = db.query(Account).all()

    db.close()
    return render_template('settings.html', system_prompt=current_prompt, accounts=accounts, saved=request.args.get('saved'))

@app.route('/accounts')
def accounts_list():
    """Page de gestion des comptes"""
    db = SessionLocal()
    accounts = db.query(Account).all()
    db.close()
    return render_template('accounts.html', accounts=accounts)

@app.route('/accounts/switch', methods=['POST'])
def switch_account():
    """Changer de compte"""
    account_id = request.form.get('account_id')
    if account_id:
        session['account_id'] = int(account_id)
    return redirect(request.referrer or url_for('index'))

@app.route('/accounts/create', methods=['POST'])
def create_account():
    """Créer un nouveau compte"""
    name = request.form.get('name')
    email = request.form.get('email')
    
    if not name or not email:
        return redirect(url_for('accounts_list', error="Champs requis manquants"))
        
    db = SessionLocal()
    try:
        new_account = Account(
            name=name,
            email=email,
            created_at=datetime.utcnow()
        )
        db.add(new_account)
        db.commit()
        session['account_id'] = new_account.id
    except Exception as e:
        print(f"Error creating account: {e}")
        return redirect(url_for('accounts_list', error="Erreur création compte"))
    finally:
        db.close()
        
    return redirect(url_for('accounts_list'))

@app.route('/accounts/rename', methods=['POST'])
def rename_account():
    """Renommer un compte"""
    account_id = request.form.get('account_id')
    new_name = request.form.get('name')
    
    if not account_id or not new_name:
         return redirect(url_for('accounts_list', error="Champs manquants"))

    db = SessionLocal()
    account = db.query(Account).get(account_id)
    if account:
        account.name = new_name
        db.commit()
    db.close()
    
    return redirect(url_for('accounts_list'))

@app.route('/accounts/delete', methods=['POST'])
def delete_account():
    """Supprimer un compte et ses données associées"""
    account_id = request.form.get('account_id')
    
    if not account_id:
        return redirect(url_for('accounts_list', error="ID manquant"))
        
    db = SessionLocal()
    account = db.query(Account).get(account_id)
    
    if not account:
        db.close()
        return redirect(url_for('accounts_list', error="Compte introuvable"))
        
    # Empêcher la suppression du dernier compte s'il n'en reste qu'un? 
    # Ou juste s'assurer qu'on switch vers un autre après.
    
    try:
        # Cascade delete manuel si pas géré par SQLAlchemy
        # Supprimer Actions
        db.query(Action).join(Prospect).filter(Prospect.account_id == account.id).delete(synchronize_session=False)
        # Supprimer Prospects
        db.query(Prospect).filter(Prospect.account_id == account.id).delete(synchronize_session=False)
        # Supprimer Campagnes
        db.query(Campaign).filter(Campaign.account_id == account.id).delete(synchronize_session=False)
        
        # Supprimer le compte
        db.delete(account)
        db.commit()
        
        # Si c'était le compte actif, changer
        if session.get('account_id') == int(account_id):
            remaining = db.query(Account).first()
            if remaining:
                session['account_id'] = remaining.id
            else:
                session.pop('account_id', None)
                
    except Exception as e:
        print(f"❌ Erreur suppression compte: {e}")
        db.rollback()
        return redirect(url_for('accounts_list', error="Erreur suppression"))
    finally:
        db.close()
        
    return redirect(url_for('accounts_list'))

@app.route('/settings/account', methods=['POST'])
def update_account_settings():
    """Mettre à jour les paramètres spécifiques au compte (Creds + Prompt)"""
    if not hasattr(g, 'account') or not g.account:
        return redirect(url_for('settings_page', error="No account selected"))
        
    db = SessionLocal()
    account = db.query(Account).get(g.account.id)
    
    if request.form.get('update_prompt'):
        # Mise à jour du prompt système uniquement
        account.system_prompt = request.form.get('system_prompt')
    else:
        # Mise à jour credentials/proxy
        account.li_at_cookie = request.form.get('li_at_cookie')
        account.user_agent = request.form.get('user_agent')
        
        account.proxy_enabled = True if request.form.get('proxy_enabled') == 'on' else False
        account.proxy_url = request.form.get('proxy_url')
        account.proxy_username = request.form.get('proxy_username')
        account.proxy_password = request.form.get('proxy_password')
        
        # Reset cookie status if manual update
        if request.form.get('li_at_cookie'):
             account.cookie_status = 'valid'
             
    db.commit()
    db.close()
    return redirect(url_for('settings_page', saved='account'))

@app.route('/accounts/security', methods=['POST'])
def update_account_security():
    """Mettre à jour UNIQUEMENT la sécurité (Timezone, Hours, Human)"""
    account_id = request.form.get('account_id')
    
    if not account_id:
        return redirect(url_for('accounts_list', error="Missing Account ID"))
        
    db = SessionLocal()
    account = db.query(Account).get(account_id)
    
    if not account:
        db.close()
        return redirect(url_for('accounts_list', error="Account not found"))
        
    try:
        # Security Settings (JSON)
        settings = {
            "timezone": request.form.get('timezone', 'Europe/Paris'),
            "working_hours": {
                "start": request.form.get('start_time', '09:00'),
                "end": request.form.get('end_time', '18:00'),
                "days": [int(d) for d in request.form.getlist('days')]
            },
            "typing_speed": {
                "min": int(request.form.get('typing_min', 50)),
                "max": int(request.form.get('typing_max', 150))
            },
            "human_scroll": True if request.form.get('human_scroll') == 'on' else False,
            "mouse_speed": "medium"
        }
        
        account.security_settings = json.dumps(settings)
        db.commit()
        
    except Exception as e:
        print(f"❌ Error updating security: {e}")
        db.rollback()
        return redirect(url_for('accounts_list', error="Update failed"))
    finally:
        db.close()
        
    return redirect(url_for('accounts_list', success="Security updated"))

                         
def get_system_prompt_global(db):
    """Helper pour récupérer le prompt global"""
    setting = db.query(Settings).filter(Settings.key == 'system_prompt').first()
    return setting.value if setting else ""

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

@app.route('/api/check_proxy/<int:account_id>')
@login_required
def check_proxy(account_id):
    """Vérifier la connexion proxy pour un compte spécifique"""
    db = SessionLocal()
    try:
        # Vérifier que le compte existe
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            return jsonify({'success': False, 'error': 'Compte introuvable'}), 404

        if not account.proxy_enabled or not account.proxy_url:
             print(f"📡 Test IP Direct (Proxy désactivé) pour {account.name}")
             proxies = None
             using_proxy = False
        else:
             using_proxy = True
             # Construction du string proxy
             proxy_url = account.proxy_url.strip()
            
             # Gestion basique du schéma si absent
             if '://' not in proxy_url:
                 proxy_url = f"http://{proxy_url}"
            
             # Séparation du schéma pour injection credentials
             scheme, address = proxy_url.split('://', 1)
            
             final_proxy = None
             if account.proxy_username and account.proxy_password:
                 final_proxy = f"{scheme}://{account.proxy_username}:{account.proxy_password}@{address}"
             else:
                 final_proxy = proxy_url

             proxies = {
                'http': final_proxy,
                'https': final_proxy
             }
             print(f"📡 Test Proxy pour {account.name}: {final_proxy}")
        
        headers = {'User-Agent': account.user_agent or 'Mozilla/5.0'}
        
        # On utilise ip-api pour avoir le pays facilement (HTTP)
        # Note: ip-api est HTTP only pour la version gratuite
        resp = requests.get('http://ip-api.com/json', headers=headers, proxies=proxies, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('status') == 'success':
                return jsonify({
                    'success': True, 
                    'ip': data.get('query'), 
                    'country': data.get('countryCode'),
                    'using_proxy': using_proxy
                })
            else:
                 return jsonify({'success': False, 'error': 'Réponse API invalide'})
        else:
             return jsonify({'success': False, 'error': f'HTTP {resp.status_code}'})
             
    except Exception as e:
         print(f"❌ Erreur test proxy: {e}")
         return jsonify({'success': False, 'error': str(e)})

    finally:
        db.close()
