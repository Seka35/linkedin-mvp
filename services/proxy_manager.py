"""
Gestion des proxies pour Playwright.
"""
import os

class ProxyManager:
    """Gestionnaire de proxies"""
    
    def __init__(self):
        self.host = os.getenv('PROXY_URL')
        self.username = os.getenv('PROXY_USERNAME')
        self.password = os.getenv('PROXY_PASSWORD')
        self.port = os.getenv('PORT')
    
    def get_proxy_config(self) -> dict:
        """Retourner config proxy pour Playwright"""
        # DÉSACTIVATION FORCÉE POUR DIAGNOSTIC (Fix Redirect Loop)
        return None
