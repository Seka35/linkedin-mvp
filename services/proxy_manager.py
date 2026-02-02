"""
Gestion des proxies pour Playwright.
"""
import os

class ProxyManager:
    """Gestionnaire de proxies"""
    
    def __init__(self):
        self.enabled = os.getenv('PROXY_ENABLED', 'false').lower() == 'true'
        self.host = os.getenv('PROXY_URL')
        self.username = os.getenv('PROXY_USERNAME')
        self.password = os.getenv('PROXY_PASSWORD')
        self.port = os.getenv('PROXY_PORT')
    
    def get_proxy_config(self) -> dict:
        """Retourner config proxy pour Playwright (format standard)"""
        if not self.enabled:
            print("ℹ️  Proxy désactivé (PROXY_ENABLED=false)")
            return None
            
        if not all([self.host, self.username, self.password, self.port]):
            print("⚠️ Configuration proxy incomplète, proxy désactivé")
            return None
        
        # Format Playwright: server séparé des credentials
        # Pour HTTPS, on utilise http:// comme protocole du proxy (standard)
        proxy_config = {
            'server': f'http://{self.host}:{self.port}',
            'username': self.username,
            'password': self.password
        }
        
        return proxy_config
