
import os
import sys
import time
import random
import json
from database.db import SessionLocal
from database.models import Account

# Mock Bot class to simulate behavior without opening browser
class HumanBehaviorTester:
    def __init__(self, account):
        self.account = account
        settings = json.loads(account.security_settings) if account.security_settings else {}
        self.typing_speed = settings.get('typing_speed', {'min': 50, 'max': 150})
        self.human_scroll = settings.get('human_scroll', True)
        
        print(f"\n🧪 TEST FACTICE POUR: {account.name}")
        print(f"⚙️ Configuration chargée:")
        print(f"   - Vitesse Frappe: {self.typing_speed['min']}ms à {self.typing_speed['max']}ms")
        print(f"   - Human Scroll: {'✅ Activé' if self.human_scroll else '❌ Désactivé'}")
        print("-" * 50)

    def test_typing(self, text):
        print(f"\n⌨️ Simulation de frappe pour : '{text}'")
        start_time = time.time()
        
        for char in text:
            # Simulation délai (ms -> s)
            delay_ms = random.uniform(self.typing_speed['min'], self.typing_speed['max'])
            delay_sec = delay_ms / 1000.0
            
            time.sleep(delay_sec)
            
            # Affichage effet machine à écrire
            sys.stdout.write(char)
            sys.stdout.flush()
            
            # Pause entre mots
            if char == ' ':
                pause = random.uniform(0.1, 0.3)
                time.sleep(pause)
                
        total_time = time.time() - start_time
        print(f"\n\n⏱️ Temps total : {total_time:.2f}s")
        print(f"📊 Vitesse moyenne : {len(text)/total_time * 60:.0f} chars/min")

if __name__ == "__main__":
    db = SessionLocal()
    # Get first active account or just first account
    account = db.query(Account).first()
    
    if not account:
        print("❌ Aucun compte trouvé dans la base de données.")
    else:
        tester = HumanBehaviorTester(account)
        tester.test_typing("Hello! Ceci est un test de vitesse de frappe.")
        
    db.close()
