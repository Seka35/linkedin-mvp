"""
Test: Envoyer un message à Joseph (déjà suivi)
Sans faire de Follow avant
"""
import requests

API_URL = "http://127.0.0.1:5000/api/message"

print("=" * 70)
print("TEST: Message à Joseph Choueifaty (déjà suivi)")
print("=" * 70)

print("\n📤 Envoi du message...")
print("   Prospect: Joseph Choueifaty (ID: 2)")
print("   Message: 'Hello Joseph!'")
print("\n🔍 Le bot va utiliser 5 méthodes de clic si nécessaire:")
print("   1. Clic forcé (ignore overlays)")
print("   2. Clic avec attente navigation")
print("   3. Clic sans attente navigation")
print("   4. Navigation directe via href")
print("   5. Clic JavaScript")
print("\n⏳ En cours...\n")

try:
    response = requests.post(API_URL, json={
        "prospect_id": 2,
        "message": "Hello Joseph!"
    }, timeout=120)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("\n" + "=" * 70)
            print("🎉 SUCCESS!")
            print("=" * 70)
            print("\n✅ Message envoyé et enregistré!")
            print("\n👉 Vérifie:")
            print("   • http://127.0.0.1:5000/messages")
            print("   • Tu devrais voir:")
            print("     - Typhaine: 'Bonjour'")
            print("     - Joseph: 'Hello Joseph!'")
        else:
            print("\n❌ FAILED")
            print("   Le bot n'a pas réussi à envoyer le message.")
            print("   Vérifie les logs du serveur Flask.")
    else:
        print(f"\n❌ ERROR: HTTP {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.Timeout:
    print("\n⏱️ TIMEOUT (>120s)")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
