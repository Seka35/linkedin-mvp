"""
Bot LinkedIn utilisant Playwright avec authentification par cookie.
Plus sûr et plus rapide que login email/password.
"""

from playwright.sync_api import sync_playwright, Page, BrowserContext
import os
import time
import random
import json
import re
from urllib.parse import urlparse
from .proxy_manager import ProxyManager

class LinkedInBot:
    """Bot d'automatisation LinkedIn avec authentification cookie"""
    
    def __init__(self, li_at_cookie=None, proxy_config: dict=None, user_agent: str=None, headless: bool = True, **kwargs):
        # Priorité aux arguments passés, sinon .env (fallback)
        self.li_at_cookie = li_at_cookie or os.getenv('LINKEDIN_LI_AT_COOKIE')
        self.headless = headless
        self.proxy_manager = ProxyManager() # Note: ProxyManager might need update too if it relies solely on env
        self.user_agent = user_agent
        
        # Override proxy configuration if provided
        self.manual_proxy_config = proxy_config
        
        # Security Settings (defaults)
        self.security_settings = kwargs.get('security_settings', {})
        self.typing_speed = self.security_settings.get('typing_speed', {'min': 50, 'max': 150})
        self.mouse_speed = self.security_settings.get('mouse_speed', 'medium')
        self.human_scroll = self.security_settings.get('human_scroll', True)
        
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        if not self.li_at_cookie:
            # On ne lève pas d'erreur ici pour permettre l'import, mais start() échouera
            print("⚠️ LINKEDIN_LI_AT_COOKIE non configuré")
    
    def start(self):
        """Démarrer le navigateur avec cookie de session"""
        if not self.li_at_cookie:
             raise ValueError("❌ LINKEDIN_LI_AT_COOKIE non configuré")

        print("🚀 Démarrage du bot LinkedIn (mode cookie)...")
        
        self.playwright = sync_playwright().start()
        
        # Configuration proxy
        if self.manual_proxy_config:
             proxy_config = self.manual_proxy_config
             print(f"🔒 Utilisation du proxy manuel: {proxy_config['server']}")
        else:
             proxy_config = self.proxy_manager.get_proxy_config()
             if proxy_config:
                 print(f"🔒 Utilisation du proxy (env): {proxy_config['server']}")
        
        # Lancer navigateur
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            proxy=proxy_config,
            args=['--disable-blink-features=AutomationControlled'] # Tentative d'évitement détection
        )
        
        # Utiliser l'UA custom ou le fallback par défaut
        ua = self.user_agent or 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0'
        
        # Créer contexte avec fingerprinting basique
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            # UA fourni par l'utilisateur (Firefox Linux) pour matcher le cookie
            user_agent=ua,
            locale='fr-FR',
            timezone_id='Europe/Paris'
        )
        
        # Injecter le cookie de session LinkedIn
        self._inject_cookie()
        
        self.page = self.context.new_page()
        
        # Vérifier que le cookie fonctionne
        if self._verify_session():
            print("✅ Bot démarré et authentifié via cookie")
            return True
        else:
            print("❌ Échec de l'authentification cookie")
            self.stop()
            return False
            
    def stop(self):
        """Arrêter le navigateur"""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            self.browser = None
            self.playwright = None
            self.context = None
            self.page = None
        except:
            pass
        print("🛑 Bot arrêté")

    def _inject_cookie(self):
        """Injecter le cookie li_at de manière robuste"""
        clean_cookie_value = self.li_at_cookie.strip().replace('"', '')
        
        # On injecte le cookie pour .linkedin.com et www.linkedin.com pour être sûr
        cookies = [
            {
                'name': 'li_at',
                'value': clean_cookie_value,
                'domain': '.linkedin.com',
                'path': '/',
                'httpOnly': True,
                'secure': True,
                'sameSite': 'None'
            }
        ]
        
        self.context.add_cookies(cookies)
        print("🍪 Cookie li_at injecté")
    
    def _verify_session(self) -> bool:
        """Vérifier que la session est valide avec gestion retry"""
        print("🔐 Vérification de la session...")
        
        try:
            # Essayer d'aller sur la homepage d'abord, moins sujet aux redirects loops que /feed direct
            response = self.page.goto('https://www.linkedin.com/', wait_until='domcontentloaded', timeout=30000)
            self._random_delay(2, 3)
            
            current_url = self.page.url
            
            # Si on est redirigé vers /feed, c'est gagné
            if '/feed' in current_url:
                print("✅ Session valide (Feed détecté)")
                return True
                
            # Si on est toujours sur home, essayons d'aller sur feed explicitement
            if 'linkedin.com' in current_url and '/login' not in current_url:
                print("➡️ Navigation explicite vers /feed...")
                self.page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded')
                self._random_delay(2, 3)
                
                if '/feed' in self.page.url:
                    print("✅ Session valide après navigation")
                    return True
            
            # Vérification finale
            if '/login' in self.page.url or 'guest' in self.page.url:
                 print(f"❌ Redirection vers login/guest : {self.page.url}")
                 return False
            
            # Par défaut on assume OK si on n'est pas sur login
            return True
            
        except Exception as e:
            print(f"❌ Erreur session (retry...): {e}")
            return False

    def visit_profile(self, profile_url: str) -> bool:
        """Visiter un profil"""
        try:
            print(f"👁️ Visite: {profile_url}")
            self.page.goto(profile_url, wait_until='domcontentloaded')
            self._random_delay(3, 6)
            self.smart_scroll() # Simulation lecture profil
            return True
        except Exception as e:
            print(f"❌ Erreur visite: {e}")
            return False

    def _extract_profile_id(self) -> str:
        """Extraire l'ID du profil depuis le code source de la page"""
        try:
            # 1. Chercher dans l'URL si elle contient l'ID (rare mais possible)
            # ex: unknown
            
            # 2. Chercher dans les balises <code> qui contiennent du JSON
            print("🔍 Recherche de l'ID du profil dans le code source...")
            
            # Pattern pour urn:li:fsd_profile:ACoAADk...
            # On cherche un pattern qui ressemble à un ID numérique ou alphanumérique long
            content = self.page.content()
            
            # Pattern 1: fs_profile (ex: "urn:li:fs_profile:ACoAAA...") et variations encoder
            patterns = [
                r'urn:li:fsd_profile:([^"\s,]+)',
                r'urn:li:fs_profile:([^"\s,]+)',
                r'\"memberId\":\"(\d+)\"',
                r'urn%3Ali%3Afsd_profile%3A([^&%\s"]+)',
                r'urn%3Ali%3Afs_profile%3A([^&%\s"]+)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # Filtrer les faux positifs (trop courts ou trop longs)
                    if len(match) > 5 and len(match) < 100:
                        # Si commence par AC, c'est souvent le bon (ID encodé)
                        # Si c'est numérique, c'est aussi bon
                        print(f"🆔 ID trouvé : {match}")
                        return match
                        
            print("⚠️ ID du profil non trouvé dans la source")
            return None
            
        except Exception as e:
            print(f"❌ Erreur extraction ID: {e}")
            return None

    def _random_delay(self, min_sec: float = 1, max_sec: float = 3):
        time.sleep(random.uniform(min_sec, max_sec))

    def human_type(self, selector: str, text: str):
        """Simuler une frappe humaine avec vitesse variable et fautes (optionnel)"""
        try:
            # Focus élément
            self.page.click(selector)
            
            for char in text:
                # Vitesse variable (ms)
                delay = random.uniform(self.typing_speed['min'], self.typing_speed['max']) # ms
                
                # TODO: Ajouter typo logic ici (e.g. 5% chance)
                
                self.page.keyboard.type(char, delay=delay)
                
                # Pause aléatoire entre les mots
                if char == ' ':
                     time.sleep(random.uniform(0.1, 0.3))
                     
        except Exception as e:
            print(f"⚠️ Erreur human_type: {e}, fallback standard")
            self.page.fill(selector, text)

    def smart_scroll(self):
        """Scroll aléatoire pour simuler la lecture"""
        if not self.human_scroll: return
        
        print("📜 Simulation lecture (Smart Scroll)...")
        try:
            # Scroll Down
            for _ in range(random.randint(2, 5)):
                scroll_amount = random.randint(300, 700)
                self.page.mouse.wheel(0, scroll_amount)
                time.sleep(random.uniform(0.5, 1.5))
            
            # Scroll Up (parfois)
            if random.random() > 0.7:
                 self.page.mouse.wheel(0, -random.randint(200, 500))
                 time.sleep(random.uniform(0.5, 1.0))
                 
        except Exception as e:
            print(f"⚠️ Erreur smart_scroll: {e}")


    def send_connection_request(self, profile_url: str, message: str = None) -> bool:
        """Envoyer une demande de connexion (Support FR/EN)"""
        try:
            if not self.visit_profile(profile_url):
                return False
                
            print("🤝 Tentative de connexion...")
            
            # --- STRATÉGIE 1 : URL DIRECTE (Seulement si ID numérique) ---
            profile_id = self._extract_profile_id()
            
            # Pour l'instant, la navigation directe via normGuestID ne fonctionne fiable qu'avec des ID numériques
            # Les ID fs_profile (ACo...) nécessitent une autre URL ou le clic UI
            if profile_id and profile_id.isdigit():
                invite_url = f"https://www.linkedin.com/people/invite?normGuestID={profile_id}"
                print(f"🔗 Navigation directe vers URL d'invitation (ID Numeric): {invite_url}")
                try:
                    self.page.goto(invite_url, wait_until='domcontentloaded')
                    self._random_delay(2, 4)
                except Exception as e:
                    print(f"⚠️ Erreur navigation directe: {e}")
            elif profile_id:
                 print(f"ℹ️ ID non-numérique détecté ({profile_id}), bascule vers clic UI standard.")

            # --- STRATÉGIE 2 : UI CLICK (Robust Text-Based) ---
            print("🖱️ Recherche du bouton Connect dans l'interface...")
            
            connect_btn = None
            
            # Recherche globale scopée au Main pour éviter header/footer
            # On cherche des boutons ou liens qui contiennent exactement "Connect" ou "Se connecter"
            # Note: Les classes artdeco-button / pv-top-card semblent absentes/obfusqués sur certains profils
            
            main_loc = self.page.locator("main").first
            if not main_loc.is_visible():
                main_loc = self.page.locator("body") 

            # Liste prioritaire de sélécteurs textuels
            text_patterns = [
                re.compile(r"^Connect$", re.IGNORECASE), 
                re.compile(r"^Se connecter$", re.IGNORECASE)
            ]
            
            # 1. Recherche boutons/liens directs
            for pattern in text_patterns:
                # On cherche button, a, ou div[role='button']
                candidates = main_loc.locator("button, a, div[role='button']").filter(has_text=pattern)
                count = candidates.count()
                
                for i in range(count):
                    candidate = candidates.nth(i)
                    if candidate.is_visible():
                        # Vérifier que ce n'est pas un bouton "Message" ou autre avec le texte dedans par hasard
                        # On vérifie le texte exact via evaluate pour être sûr
                        text = candidate.inner_text().strip()
                        if re.match(pattern, text):
                            connect_btn = candidate
                            print(f"✅ Bouton Connect trouvé par texte ({text})")
                            break
                if connect_btn: break
            
            # 2. Si pas trouvé, chercher dans le menu "Plus"
            # --- 2. Recherche du bouton Connect (SCOPÉ) ---
            print("🖱️ Recherche du bouton Connect dans l'interface...")
            
            # On définit la zone de recherche principale (Profile Card)
            main_profile_card = self.page.locator("main section").first
            connect_btn = None
            
            # Stratégie 1: Bouton direct dans la card principale
            # On cherche "Connect" ou "Se connecter"
            # Note: On exclut les boutons "Message" ou "More" qui pourraient contenir "Connect" dans des attributs cachés
            primary_btn = main_profile_card.locator("button, a").filter(has_text=re.compile(r"^(Connect|Se connecter)$", re.IGNORECASE)).first
            
            if primary_btn.is_visible():
                connect_btn = primary_btn
                print("✅ Bouton Connect trouvé (Principal)")
            
            # Stratégie 2: Menu "More" / "Plus"
            if not connect_btn:
                # Le bouton "More" est souvent le dernier de la liste d'actions
                more_btn = main_profile_card.locator("button[aria-label*='More'], button[aria-label*='Plus']").first
                if not more_btn.is_visible():
                     # Fallback selecteur générique pour le bouton "..."
                     more_btn = main_profile_card.locator(".artdeco-dropdown__trigger").first
                
                if more_btn.is_visible():
                    print("ℹ️ Connect absent, vérification du menu 'Plus'...")
                    try:
                        more_btn.click()
                        self._random_delay(0.5, 1)
                        
                        # Le menu s'ouvre souvent dans un layer global (.artdeco-dropdown__content)
                        # On doit chercher dans le document entier, mais filtrer par texte strict
                        dropdown_opts = self.page.locator("div.artdeco-dropdown__content div[role='button'], div.artdeco-dropdown__content a").filter(has_text=re.compile(r"^(Connect|Se connecter)$", re.IGNORECASE))
                        
                        # On prend le premier visible
                        for i in range(dropdown_opts.count()):
                            opt = dropdown_opts.nth(i)
                            if opt.is_visible():
                                connect_btn = opt
                                print("✅ Bouton Connect trouvé dans le menu Plus")
                                break
                    except Exception as e:
                        print(f"⚠️ Erreur menu Plus: {e}")

            # Stratégie 3: Gestion des états déjà connectés/pending (Evite les faux positifs)
            if not connect_btn:
                 # Si on voit "Message" en bouton principal et PAS de connect, c'est souvent qu'on est déjà connecté ou pending
                 # Mais on laisse la suite du code (Follow) gérer ça.
                 pass     # --- 3. Clic et Validation ---
            # --- 3. Clic et Validation ---
            if connect_btn and connect_btn.is_visible():
                print("🖱️ Smart Click (Suppression href pour éviter navigation)...")
                
                # Hack anti-white-page: On supprime l'attribut href pour empêcher la navigation
                # et forcer l'usage du gestionnaire d'événement JS (React/Ember)
                connect_btn.scroll_into_view_if_needed()
                
                # Tentative ultime : Navigation au clavier (Humain)
                if connect_btn:
                    # Si on a ciblé l'SVG (connect-small), on doit remonter au bouton parent pour le focus
                    try:
                        is_svg = connect_btn.evaluate("el => el.tagName.toLowerCase() === 'svg' || el.id === 'connect-small'")
                        if is_svg:
                            print("🔍 SVG détecté, remonte au parent <button> ou <a>...")
                            connect_btn = connect_btn.locator("xpath=..")
                    except Exception as e:
                        print(f"Check SVG warning: {e}")

                    # Debug: Afficher ce qu'on va cliquer
                    try:
                        html_snapshot = connect_btn.evaluate("el => el.outerHTML")
                        print(f"🎯 CIBLAGE: {html_snapshot[:150]}...") 
                    except:
                        pass

                    print("⌨️ Entrée Clavier (Focus + Enter)...")
                    try:
                        connect_btn.focus()
                        self._random_delay(0.2, 0.5)
                        self.page.keyboard.press("Enter")
                    except Exception as e:
                        print(f"Keyboard press failed: {e}. Fallback to JS click.")
                        self.page.evaluate("(element) => element.click()", connect_btn.element_handle())
                
                self._random_delay(2, 4) # Attendre que la modale s'ouvre ou que l'état change
                
                # --- 4. Gestion de la Modale (PRIORITAIRE) ---
                print("🔍 Recherche de la modale d'envoi...")
                
                # Sélecteurs pour la modale via TEXTE (plus robuste que aria-label)
                # Bouton "Ajouter une note"
                add_note_btn = self.page.locator("button, div[role='button']").filter(has_text=re.compile(r"^(Add a note|Ajouter une note)$", re.IGNORECASE)).first
                
                # Bouton "Envoyer sans note"
                send_now_btn = self.page.locator("button, div[role='button']").filter(has_text=re.compile(r"^(Send without a note|Envoyer sans note)$", re.IGNORECASE)).first
                
                # Si non trouvé, fallback partiel (contains)
                if not add_note_btn.is_visible():
                     add_note_btn = self.page.locator("button").filter(has_text="Ajouter une note").first
                     if not add_note_btn.is_visible():
                         add_note_btn = self.page.locator("button").filter(has_text="Add a note").first

                if not send_now_btn.is_visible():
                    send_now_btn = self.page.locator("button").filter(has_text="Envoyer sans note").first
                    if not send_now_btn.is_visible():
                        send_now_btn = self.page.locator("button").filter(has_text="Send without a note").first
                
                # Si des boutons de modale sont visibles, on DOIT les traiter, peu importe le statut Pending du background
                if add_note_btn.is_visible() or send_now_btn.is_visible():
                    print("✅ Modale détectée. Traitement...")
                    
                    invite_sent = False
                    # IMPORTANT: On ignore le message, on envoie TOUJOURS sans note (demande user)
                    if message:
                        print("⚠️ Message fourni mais ignoré (Mode Send Without Note forcé).")

                    if send_now_btn.is_visible():
                        print("🚀 Envoi sans note...")
                        send_now_btn.click()
                        invite_sent = True
                    else:
                        # Fallback Send dans modale
                        send_btn = self.page.locator("div[role='dialog'] button").filter(has_text=re.compile(r"^(Envoyer|Send)$", re.IGNORECASE)).first
                        if send_btn.is_visible():
                            print("🚀 Envoi (Bouton générique modale)...")
                            send_btn.click()
                            invite_sent = True

                    if invite_sent:
                        print("✅ Invitation envoyée avec succès (via Modale)")
                        self._random_delay(1, 2)
                        return (True, 'connected')
                    else:
                        print("❌ Impossible de cliquer sur Envoyer (Boutons introuvables)")
                        return (False, 'failed')

                # --- 3b (Fallback). Vérification 'Pending' (Si PAS de modale détectée) ---
                print("🔍 Modale non détectée. Vérification de l'état 'Pending' (Succès immédiat?)...")
                
                pending_patterns = [
                    re.compile(r"^Pending$", re.IGNORECASE),
                    re.compile(r"^En attente$", re.IGNORECASE)
                ]
                
                for pattern in pending_patterns:
                    if main_loc.locator("button, div, span").filter(has_text=pattern).first.is_visible():
                        print(f"✅ État PENDING détecté ! Invitation envoyée avec succès.")
                        return (True, 'connected')
                        
                if main_loc.locator("button[aria-label*='Pending'], button[aria-label*='En attente']").first.is_visible():
                     print(f"✅ État PENDING détecté (aria-label) ! Invitation envoyée.")
                     return (True, 'connected')
                
                print("❌ Échec : Pas de modale et pas de passage en Pending.")
                return (False, 'failed')

            else:
                # Si Connect n'est pas trouvé, on cherche FOLLOW
                print("⚠️ Bouton 'Connect' introuvable. Recherche bouton 'Follow'...")
                follow_btn = main_loc.locator("button, div[role='button']").filter(has_text=re.compile(r"^(Follow|Suivre)$", re.IGNORECASE)).first
                
                if follow_btn.is_visible():
                     print("➕ Bouton Follow trouvé ! Clic...")
                     try:
                        follow_btn.click()
                        self._random_delay(1, 2)
                        print("✅ Suivi effectué (Followed)")
                        return (True, 'followed')
                     except Exception as e:
                        print(f"❌ Erreur click Follow: {e}")
                        return (False, 'failed')

                print("❌ Ni Connect ni Follow trouvés (déjà connecté ?)")
                return (False, 'failed')
                
        except Exception as e:
            print(f"❌ Erreur connexion: {e}")
            return (False, 'failed')

    def send_message(self, profile_url: str, message: str) -> bool:
        """Envoyer un DM à une relation existante"""
        try:
            if not self.visit_profile(profile_url):
                return False
                
            print("💬 Tentative d'envoi message...")
            
            # --- 1. Ciblage du bouton "Message" sur le profil ---
            # On cible la zone principale du profil pour éviter les boutons "Message" dans la sidebar ou le feed
            main_profile_card = self.page.locator("main section").first 
            
            msg_btn = None
            
            # Ordre de priorité des sélecteurs (du plus précis "profil" au plus général)
            selectors = [
                 # Bouton principal action bar (souvent .pvs-profile-actions ou .pv-top-card-v2-ctas)
                main_profile_card.locator("button, a").filter(has_text=re.compile(r"^(Message|Envoyer un message)$", re.IGNORECASE)),
                
                # Fallback : URL spécifique messaging
                self.page.locator("a[href*='/messaging/compose']"),
            ]
            
            for sel in selectors:
                 # On prend le premier visible
                 count = sel.count()
                 for i in range(count):
                      if sel.nth(i).is_visible():
                          msg_btn = sel.nth(i)
                          print(f"✅ Bouton Message trouvé (sélecteur #{selectors.index(sel)}, index {i})")
                          break
                 if msg_btn: break
            
            # Fallback ultime (Global) mais risqué -> on le garde en dernier recours
            if not msg_btn:
                 print("⚠️ Tentative fallback global...")
                 msg_btn = self.page.locator("main button").filter(has_text=re.compile(r"^(Message|Envoyer un message)$", re.IGNORECASE)).first

            if msg_btn and msg_btn.is_visible():
                print("🖱️ Clic sur le bouton Message...")
                
                # Debug: afficher les attributs du bouton
                try:
                    btn_html = msg_btn.evaluate("el => el.outerHTML")
                    print(f"   Bouton HTML: {btn_html[:200]}...")
                except:
                    pass
                
                # Attendre que la page soit stable
                try:
                    self.page.wait_for_load_state("networkidle", timeout=5000)
                except:
                    pass
                
                # Scroll et focus avant de cliquer
                try:
                    msg_btn.scroll_into_view_if_needed()
                    self._random_delay(0.8, 1.2)
                    msg_btn.focus()
                    self._random_delay(0.5, 0.8)
                except:
                    pass
                
                # Tentative de clic avec gestion d'erreur
                click_success = False
                
                # Essai 1: Clic forcé (ignore les overlays)
                try:
                    msg_btn.click(force=True, timeout=3000)
                    click_success = True
                    print("   ✓ Clic forcé réussi")
                except Exception as e:
                    print(f"   ✗ Échec clic forcé: {e}")
                    
                    # Essai 2: Clic normal avec attente de navigation
                    try:
                        with self.page.expect_navigation(timeout=5000):
                            msg_btn.click()
                        click_success = True
                        print("   ✓ Clic réussi (avec navigation)")
                    except:
                        # Essai 3: Clic sans attente de navigation
                        try:
                            msg_btn.click()
                            click_success = True
                            print("   ✓ Clic réussi (sans navigation)")
                        except Exception as e3:
                            print(f"   ✗ Échec clic standard: {e3}")
                            
                            # Essai 4: Navigation directe via href
                            try:
                                href = msg_btn.get_attribute("href")
                                if href:
                                    print(f"   → Tentative navigation directe: {href[:50]}...")
                                    self.page.goto(f"https://www.linkedin.com{href}" if href.startswith("/") else href)
                                    click_success = True
                                    print("   ✓ Navigation directe réussie")
                            except Exception as e4:
                                print(f"   ✗ Échec navigation: {e4}")
                                
                                # Essai 5: Clic JavaScript en dernier recours
                                try:
                                    self.page.evaluate("(el) => el.click()", msg_btn.element_handle())
                                    click_success = True
                                    print("   ✓ Clic JS réussi")
                                except Exception as e5:
                                    print(f"   ✗ Échec clic JS: {e5}")
                
                if not click_success:
                    print("❌ Impossible de cliquer sur le bouton Message après 5 tentatives")
                    return False
                
                self._random_delay(1, 2)
                
                # --- 2. Détection de la popup Premium (Blocker) ---
                print("🔍 Vérification popup Premium...")
                premium_popup = self.page.locator("div[role='dialog']").filter(has_text=re.compile(r"(Message .* with Premium|Premium)", re.IGNORECASE)).first
                
                if premium_popup.is_visible(timeout=2000):
                    print("❌ BLOQUÉ: Popup Premium détectée!")
                    print("   → Vous ne pouvez pas envoyer de message à ce prospect sans LinkedIn Premium.")
                    print("   → Le prospect est probablement une connexion de 3ème degré (3rd).")
                    # Fermer la popup
                    try:
                        close_btn = premium_popup.locator("button[aria-label*='Dismiss'], button[data-test-modal-close-btn]").first
                        if close_btn.is_visible():
                            close_btn.click()
                    except:
                        pass
                    return False
                
                # --- 3. Détection de la zone de message ---
                print("🔍 Recherche de l'éditeur...")
                
                # On cherche le CONTENEUR du formulaire pour scoper la recherche du bouton Envoyer
                msg_form = self.page.locator("form.msg-form, div[role='dialog'], div.msg-overlay-conversation-bubble").first
                
                # Attendre l'apparition de l'un des éléments clés (Sujet ou Body)
                try:
                     self.page.wait_for_selector("input[name='subject'], div.msg-form__contenteditable, div[role='textbox']", timeout=10000)
                except:
                    print("⚠️ Timeout attente éditeur message")

                # 1. Gestion du Sujet (si présent)
                subject_input = self.page.locator("input[name='subject']").first
                if subject_input.is_visible():
                    print("📝 Champ Sujet détecté. (Focus et Tab)")
                    subject_input.focus()
                    self._random_delay(0.2, 0.5)
                    self.page.keyboard.press("Tab")
                    self._random_delay(0.2, 0.5)

                # 2. Focus et Remplissage Body
                editor = self.page.locator("div.msg-form__contenteditable").first
                if not editor.is_visible():
                     editor = self.page.locator("div[role='textbox'][aria-label*='Write a message']").first
                     if not editor.is_visible():
                         editor = self.page.evaluate_handle("document.activeElement")

                if editor and editor.is_visible():
                    print("📝 Remplissage du message...")
                    editor.click()
                    self._random_delay(0.2, 0.5)
                    self.human_type("div.msg-form__contenteditable" if editor else "textarea", message)
                    self._random_delay(1, 2)
                    
                    # 3. Envoi (SCOPÉ au formulaire)
                    # On cherche le bouton UNIQUEMENT dans le conteneur msg_form détecté ou via classes précises
                    send_btn = self.page.locator("button.msg-form__send-button").first
                    
                    if not send_btn.is_visible():
                        # Utilisation du scope msg_form si possible
                        if msg_form.is_visible():
                             send_btn = msg_form.locator("button").filter(has_text=re.compile(r"^(Send|Envoyer)$", re.IGNORECASE)).first
                        else:
                             # Fallback global mais dangereux (risque "Share post")
                             # On essaie d'éviter les modales de partage
                             send_btn = self.page.locator("button").filter(has_text=re.compile(r"^(Send|Envoyer)$", re.IGNORECASE)).exclude(self.page.locator("div.share-creation-state button")).first
                    
                    if send_btn.is_visible():
                        print("🚀 Clic sur Envoyer...")
                        send_btn.click()
                        print("✅ Message envoyé")
                        return True
                    else:
                        print("⚠️ Bouton Envoyer introuvable, tentative TAB + Enter...")
                        self.page.keyboard.press("Tab")
                        self._random_delay(0.5, 1)
                        self.page.keyboard.press("Enter")
                        return True

                else:
                    print("❌ Éditeur message introuvable")
                    # Debug snapshot
                    try:
                        with open("debug_msg_error.html", "w") as f: f.write(self.page.content())
                    except: pass
                    return False
            
            print("❌ Impossible d'envoyer le message (pas connecté ou bouton introuvable)")
            return False
            
        except Exception as e:
            print(f"❌ Erreur envoi message: {e}")
            return False
