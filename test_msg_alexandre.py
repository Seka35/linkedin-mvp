"""
Test d'envoi de message à Alexandre Pereira (déjà connecté)
Via l'API du dashboard avec le code amélioré
"""
import requests

API_URL = "http://127.0.0.1:5000/api/message"

data = {
    "prospect_id": 4,  # Alexandre Pereira (connected)
    "message": "Hello Alexandre! This is a test message from the improved bot."
}

print("📤 Envoi du message via l'API du dashboard...")
print(f"   Prospect: Alexandre Pereira (ID: {data['prospect_id']})")
print(f"   Message: {data['message']}")
print("\n🔍 Le bot va maintenant:")
print("   1. Détecter le bouton Message")
print("   2. Afficher le HTML du bouton (debug)")
print("   3. Scroller et focus")
print("   4. Tenter le clic (3 méthodes si nécessaire)")
print("   5. Remplir et envoyer le message")
print("\n⏳ Attente de la réponse...\n")

try:
    response = requests.post(API_URL, json=data, timeout=120)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("\n✅ SUCCESS! Message envoyé et enregistré.")
            print("👉 Vérifie la page http://127.0.0.1:5000/messages")
        else:
            print("\n❌ FAILED: Le bot n'a pas réussi.")
    else:
        print(f"\n❌ ERROR: Status {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.Timeout:
    print("\n⏱️ TIMEOUT: Le bot prend trop de temps (>120s)")
except requests.exceptions.ConnectionError:
    print("\n❌ ERROR: Serveur Flask non accessible")
    print("   Lance: ./venv/bin/python main.py")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
