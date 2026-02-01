"""
Test complet: Follow Joseph puis lui envoyer un message
Joseph est une connexion 2nd, donc pas de blocage Premium
"""
import requests
import time

API_BASE = "http://127.0.0.1:5000/api"

print("=" * 70)
print("TEST: Follow + Message pour Joseph Choueifaty (2nd)")
print("=" * 70)

# Étape 1: Follow
print("\n🔹 ÉTAPE 1: Follow")
print("   Profil: https://www.linkedin.com/in/josephchoueifaty/?locale=en")

connect_response = requests.post(f"{API_BASE}/connect", json={
    "prospect_id": 2,  # Joseph
    "message": ""
})

if connect_response.status_code == 200:
    result = connect_response.json()
    if result.get('success'):
        print("   ✅ Follow réussi!")
    else:
        print("   ⚠️ Follow a échoué (peut-être déjà suivi?), on continue...")
else:
    print(f"   ❌ Erreur API: {connect_response.status_code}")

# Attendre
print("\n⏳ Attente de 3 secondes...")
time.sleep(3)

# Étape 2: Message
print("\n🔹 ÉTAPE 2: Envoi du message")
print("   Message: 'Hello Joseph!'")
print("\n📋 Le bot va:")
print("   1. Cliquer sur Message")
print("   2. Vérifier la popup Premium (devrait PAS apparaître pour 2nd)")
print("   3. Remplir et envoyer le message")
print("\n⏳ En cours...\n")

msg_response = requests.post(f"{API_BASE}/message", json={
    "prospect_id": 2,
    "message": "Hello Joseph!"
}, timeout=120)

if msg_response.status_code == 200:
    msg_result = msg_response.json()
    if msg_result.get('success'):
        print("\n" + "=" * 70)
        print("🎉 TEST RÉUSSI!")
        print("=" * 70)
        print("\n✅ Message envoyé et enregistré dans la base de données!")
        print("\n👉 Vérifie:")
        print("   • Page Messages: http://127.0.0.1:5000/messages")
        print("   • Tu devrais voir 2 messages:")
        print("     - Typhaine: 'Bonjour'")
        print("     - Joseph: 'Hello Joseph!'")
    else:
        print("\n❌ Échec de l'envoi du message")
        print("   Vérifie les logs du serveur Flask pour plus de détails")
else:
    print(f"\n❌ Erreur API: {msg_response.status_code}")
    print(f"Response: {msg_response.text}")
