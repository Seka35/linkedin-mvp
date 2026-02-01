"""
Test complet: Connect puis Message pour Diego
"""
import requests
import time

API_BASE = "http://127.0.0.1:5000/api"

# 1. D'abord, envoyer une demande de connexion
print("🤝 Étape 1: Envoi de la demande de connexion...")
connect_response = requests.post(f"{API_BASE}/connect", json={
    "prospect_id": 6,  # Diego
    "message": ""  # Pas de note
})

if connect_response.status_code == 200:
    result = connect_response.json()
    if result.get('success'):
        print("✅ Connexion envoyée avec succès!")
        print("⏳ Attente de 5 secondes avant d'envoyer le message...")
        time.sleep(5)
        
        # 2. Ensuite, envoyer un message
        print("\n💬 Étape 2: Envoi du message...")
        msg_response = requests.post(f"{API_BASE}/message", json={
            "prospect_id": 6,
            "message": "Hola Diego! Encantado de conectar contigo."
        })
        
        if msg_response.status_code == 200:
            msg_result = msg_response.json()
            if msg_result.get('success'):
                print("✅ Message envoyé avec succès!")
                print("👉 Vérifie la page /messages dans le dashboard!")
            else:
                print("❌ Échec de l'envoi du message")
        else:
            print(f"❌ Erreur API message: {msg_response.status_code}")
    else:
        print("❌ Échec de la connexion")
        print("Note: Si Diego a déjà un bouton 'Follow' au lieu de 'Connect', c'est normal.")
else:
    print(f"❌ Erreur API connect: {connect_response.status_code}")
