"""
Test d'envoi de message via l'API du dashboard
Ceci simule un clic sur le bouton "💬 Msg" dans l'interface web
"""
import requests
import json

# URL de l'API locale
API_URL = "http://127.0.0.1:5000/api/message"

# Données du message
data = {
    "prospect_id": 6,  # Diego Maldonado
    "message": "Hola Diego! Este es un mensaje de prueba del bot de LinkedIn."
}

print("📤 Envoi du message via l'API du dashboard...")
print(f"   Prospect ID: {data['prospect_id']}")
print(f"   Message: {data['message']}")

try:
    response = requests.post(API_URL, json=data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✅ SUCCESS! Message envoyé et enregistré dans la base de données.")
            print("   👉 Vérifie maintenant la page /messages dans le dashboard!")
        else:
            print("❌ FAILED: Le bot n'a pas réussi à envoyer le message.")
    else:
        print(f"❌ ERROR: Status code {response.status_code}")
        print(f"   Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("❌ ERROR: Impossible de se connecter au serveur Flask.")
    print("   Assure-toi que le serveur tourne avec: ./venv/bin/python main.py")
except Exception as e:
    print(f"❌ ERROR: {e}")
