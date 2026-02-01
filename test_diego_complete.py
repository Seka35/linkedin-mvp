"""
Test complet: Follow Diego puis lui envoyer un message
"""
import requests
import time

API_BASE = "http://127.0.0.1:5000/api"

print("=" * 60)
print("TEST: Follow + Message pour Diego Maldonado")
print("=" * 60)

# Étape 1: Follow (ou Connect)
print("\n🔹 ÉTAPE 1: Follow/Connect")
print("   Profil: https://www.linkedin.com/in/maldonado1diego/?locale=es")

connect_response = requests.post(f"{API_BASE}/connect", json={
    "prospect_id": 6,  # Diego Maldonado
    "message": ""  # Pas de note
})

if connect_response.status_code == 200:
    result = connect_response.json()
    if result.get('success'):
        print("   ✅ Follow/Connect réussi!")
    else:
        print("   ⚠️ Follow/Connect a échoué, mais on continue...")
else:
    print(f"   ❌ Erreur API: {connect_response.status_code}")
    exit(1)

# Attendre un peu
print("\n⏳ Attente de 3 secondes...")
time.sleep(3)

# Étape 2: Message
print("\n🔹 ÉTAPE 2: Envoi du message")
print("   Message: 'Hola Diego! Encantado de conectar.'")

msg_response = requests.post(f"{API_BASE}/message", json={
    "prospect_id": 6,
    "message": "Hola Diego! Encantado de conectar."
}, timeout=120)

if msg_response.status_code == 200:
    msg_result = msg_response.json()
    if msg_result.get('success'):
        print("   ✅ Message envoyé avec succès!")
        print("\n" + "=" * 60)
        print("🎉 TEST RÉUSSI!")
        print("=" * 60)
        print("\n👉 Vérifie maintenant:")
        print("   • Page Messages: http://127.0.0.1:5000/messages")
        print("   • Tu devrais voir le message à Diego avec la date/heure")
    else:
        print("   ❌ Échec de l'envoi du message")
        print("\n💡 Note: Si Diego n'est pas encore connecté, LinkedIn")
        print("   pourrait bloquer l'envoi de message direct.")
else:
    print(f"   ❌ Erreur API: {msg_response.status_code}")
    print(f"   Response: {msg_response.text}")
